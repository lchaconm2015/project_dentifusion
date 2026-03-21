from odoo.tests.common import TransactionCase


class TestPatientRegistration(TransactionCase):

    def test_module_installs_and_env_works(self):
        self.assertTrue(self.env)
        self.assertTrue(self.env.user)
        self.assertEqual(self.env.user._name, "res.users")
