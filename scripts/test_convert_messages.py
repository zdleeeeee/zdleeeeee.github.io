import unittest

from scripts.convert_messages import convert


class ConvertMessagesTests(unittest.TestCase):
    def test_message_lines_get_markdown_hard_breaks(self):
        source = 'name="Alice"\n\n---\nAlice\nFirst line\nSecond line\n\nNew paragraph\n'

        result = convert(source)

        self.assertIn('First line  \nSecond line  \n\nNew paragraph  \n{{< /message >}}', result)


if __name__ == "__main__":
    unittest.main()
