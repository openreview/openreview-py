import unittest
from openreview import *

class TestOpenReviewMethods(unittest.TestCase):


    def test_login_error(self):
        with self.assertRaises(OpenReviewException):
            client = Client(username='fakeEmail@mail.com',password='abcXYZ')

            

if __name__ == '__main__':
    unittest.main()