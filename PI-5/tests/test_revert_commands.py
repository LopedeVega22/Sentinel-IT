import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from tools.revert_commands import derive_revert_command


class TestRevertCommands(unittest.TestCase):
    def test_iptables_insert_is_reverted_with_delete(self):
        command = 'sudo iptables -I INPUT -s 1.2.3.4 -j DROP'

        result = derive_revert_command(command, '1.2.3.4')

        self.assertEqual(result, 'sudo iptables -D INPUT -s 1.2.3.4 -j DROP')
        self.assertFalse(result.startswith('#'))

    def test_chained_iptables_append_rules_are_reverted(self):
        command = (
            'sudo iptables -A INPUT -p tcp -s 1.2.3.4 --dport 80 -j DROP && '
            'sudo iptables -A INPUT -p tcp -s 1.2.3.4 --dport 8080 -j DROP'
        )

        result = derive_revert_command(command, '1.2.3.4')

        self.assertEqual(
            result,
            'sudo iptables -D INPUT -p tcp -s 1.2.3.4 --dport 80 -j DROP && '
            'sudo iptables -D INPUT -p tcp -s 1.2.3.4 --dport 8080 -j DROP',
        )

    def test_unknown_command_returns_empty_so_operator_must_provide_revert(self):
        result = derive_revert_command('sudo custom-block 1.2.3.4', '1.2.3.4')

        self.assertEqual(result, '')

    def test_systemctl_stop_is_reverted_with_start(self):
        result = derive_revert_command('sudo systemctl stop apache2')

        self.assertEqual(result, 'sudo systemctl start apache2')


if __name__ == '__main__':
    unittest.main()
