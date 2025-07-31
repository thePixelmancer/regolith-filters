import unittest
import multifeature as mf


class TestMultiFeatureUtils(unittest.TestCase):
    def test_path_string(self):
        test_cases = [
            ("/path/to/resource", "path/to/resource/"),
            ("path/to/resource", "path/to/resource/"),
            ("", ""),
        ]
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                self.assertEqual(mf.path_string(input_str), expected)

    def test_remove_namespace(self):
        test_cases = [
            ("@namespace:feature_rule", ("@namespace:", "feature_rule")),
            ("minecraft:scatter_feature", ("minecraft:", "scatter_feature")),
            ("feature_rule", ("", "feature_rule")),
            ("minecraft:", ("minecraft:", "")),
            ("no_namespace", ("", "no_namespace")),
        ]
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                self.assertEqual(mf.remove_namespace(input_str), expected)


if __name__ == "__main__":
    unittest.main()
