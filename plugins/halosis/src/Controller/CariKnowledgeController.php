<?php

namespace GlpiPlugin\Halosis\Controller;

use Glpi\Controller\AbstractController;
use Glpi\Http\Firewall;
use Glpi\Security\Attribute\SecurityStrategy;
use GlpiPlugin\Halosis\Ai\AiException;
use GlpiPlugin\Halosis\Ai\Service;
use GlpiPlugin\Halosis\KnowledgeSearch;
use GlpiPlugin\Halosis\Profile;
use KnowbaseItem;
use Session;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\Routing\Attribute\Route;

/**
 * Cari knowledge untuk Operator & Tim Teknis (/plugins/halosis/CariKnowledge, FR-03): pencarian semantik atas
 * artikel KB & tiket historis lewat layanan AI; bila layanan mati → pencarian kata kunci artikel KB.
 * Artikel KB hanya ditampilkan bila pengguna berhak melihatnya.
 */
final class CariKnowledgeController extends AbstractController
{
    public const PAGE = '/plugins/halosis/CariKnowledge';
    private const LIMIT = 10;

    #[SecurityStrategy(Firewall::STRATEGY_CENTRAL_ACCESS)]
    #[Route('/CariKnowledge', name: 'cari_knowledge', methods: 'GET')]
    public function __invoke(Request $request): Response
    {
        if (!Session::haveRight(Profile::RIGHT_TRIASE, READ)) {
            throw new AccessDeniedHttpException();
        }

        $query  = trim(mb_substr((string) $request->query->get('q', ''), 0, 500));
        $mode   = 'semantik';
        $result = [];
        if ($query !== '') {
            try {
                $result = self::semantic($query);
            } catch (AiException $e) {
                $mode   = 'kata kunci';
                $result = array_map(static fn ($a) => [
                    'title' => $a['name'], 'text' => $a['text'], 'url' => $a['url'], 'kind' => 'kb', 'ref' => 'KB-' . $a['id'], 'score' => null,
                ], KnowledgeSearch::search($query, self::LIMIT));
            }
        }

        return $this->render('@halosis/cari_knowledge.html.twig', [
            'title'   => __('Search knowledge', 'halosis'),
            'menu'    => ['tools', KnowbaseItem::class],
            'query'   => $query,
            'mode'    => $mode,
            'results' => $result,
            'kb_url'  => KnowbaseItem::getSearchURL(),
        ]);
    }

    /**
     * @return array<int, array{title: string, text: string, url: string, kind: string, ref: string, score: ?float}>
     */
    private static function semantic(string $query): array
    {
        $response = Service::post('/cari', ['q' => $query, 'k' => self::LIMIT]);
        $items = [];
        foreach ($response['hasil'] ?? [] as $hit) {
            $ref = (string) ($hit['sumber'] ?? '');
            $url = '';
            if (preg_match('/^KB-(\d+)$/', $ref, $m)) {
                $article = new KnowbaseItem();
                if (!$article->getFromDB((int) $m[1]) || !$article->canViewItem()) {
                    continue;
                }
                $url = KnowbaseItem::getFormURLWithID((int) $m[1]);
            }
            $items[] = [
                'title' => (string) ($hit['judul'] ?? ''),
                'text'  => (string) ($hit['potongan'] ?? ''),
                'url'   => $url,
                'kind'  => (string) ($hit['jenis_sumber'] ?? ''),
                'ref'   => $ref,
                'score' => isset($hit['skor']) ? (float) $hit['skor'] : null,
            ];
        }
        return $items;
    }
}
