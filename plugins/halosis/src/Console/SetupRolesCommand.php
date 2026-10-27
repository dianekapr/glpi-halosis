<?php

namespace GlpiPlugin\Halosis\Console;

use Glpi\Console\AbstractCommand;
use GlpiPlugin\Halosis\Roles;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use User;

/**
 * Terapkan 6 role HaloSIS ke profil GLPI. Aman dijalankan berulang.
 *
 *   php bin/console plugins:halosis:setup-roles
 */
class SetupRolesCommand extends AbstractCommand
{
    protected function configure()
    {
        parent::configure();

        $this->setName('plugins:halosis:setup-roles');
        $this->setDescription('Terapkan role HaloSIS ke profil GLPI (ganti nama, Knowledge Manager, hak akses, akun bawaan)');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        foreach (Roles::apply() as $line) {
            $output->writeln('  ' . $line);
        }

        $defaults = User::checkDefaultPasswords();
        if ($defaults !== []) {
            $output->writeln(sprintf(
                '<comment>PERINGATAN: akun berikut masih memakai password bawaan: %s. Segera ganti.</comment>',
                implode(', ', $defaults)
            ));
        }

        $output->writeln('<info>Role HaloSIS selesai diterapkan.</info>');
        return 0;
    }
}
