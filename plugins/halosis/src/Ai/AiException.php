<?php

namespace GlpiPlugin\Halosis\Ai;

use RuntimeException;

/**
 * Kegagalan pemanggilan AI (jaringan, timeout, penolakan, jawaban tidak valid).
 * Pemanggil wajib menangkapnya supaya alur GLPI (mis. penyimpanan tiket) tidak terganggu.
 */
final class AiException extends RuntimeException
{
}
