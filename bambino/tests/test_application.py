from bambino.appenv import *
import os
import unittest


class TestApplication(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_supervisor_service_names(self):
        app = Application(os.getcwd())
        path = '/etc/supervisor/conf.d'
        path_to_conf = path + '/temp.conf'

        if not os.path.exists(path):
            os.makedirs(path)

        if os.path.exists(path_to_conf):
            os.remove(path_to_conf)

        conf_file = open(path_to_conf, 'w')
        lines = ['[program:billweb]', 'start=0', '[program:other_program]']
        conf_file.write("\n".join(lines))
        conf_file.close()

        services_names = app.supervisor_service_names('temp')

        self.assertEqual(services_names[0], 'billweb')
        self.assertEqual(len(services_names), 2)
        os.remove(path_to_conf)


if __name__ == '__main__':
    unittest.main()
