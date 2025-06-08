"""Tests for the module generator."""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from ellma.core.module_generator import ModuleGenerator


class TestModuleGenerator(unittest.TestCase):
    """Test cases for the ModuleGenerator class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.generator = ModuleGenerator(base_path=str(self.test_dir))
        self.test_spec = {
            "name": "Test Module",
            "description": "A test module for unit testing",
            "purpose": "Testing the module generator",
            "dependencies": ["pytest", "numpy"]
        }

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sanitize_name(self):
        """Test name sanitization."""
        self.assertEqual(self.generator._sanitize_name("Test Module"), "test_module")
        self.assertEqual(self.generator._sanitize_name("123Module"), "m_123module")
        self.assertEqual(self.generator._sanitize_name("Module@#Test"), "moduletest")

    def test_generate_module_structure(self):
        """Test module generation creates correct directory structure."""
        result = self.generator.generate_module(self.test_spec)
        
        self.assertEqual(result["status"], "success")
        self.assertTrue((self.test_dir / "test_module").exists())
        self.assertTrue((self.test_dir / "test_module" / "tests").exists())
        self.assertTrue((self.test_dir / "test_module" / "test_module").exists())

    def test_generate_module_files(self):
        """Test all required files are generated."""
        result = self.generator.generate_module(self.test_spec)
        module_dir = self.test_dir / "test_module"
        
        expected_files = [
            module_dir / "README.md",
            module_dir / "pyproject.toml",
            module_dir / "Dockerfile",
            module_dir / "Makefile",
            module_dir / "test_module" / "__init__.py",
            module_dir / "tests" / "__init__.py",
            module_dir / "tests" / "test_test_module.py"
        ]
        
        for file_path in expected_files:
            with self.subTest(file=file_path):
                self.assertTrue(file_path.exists(), f"Expected file not found: {file_path}")

    def test_module_content(self):
        """Test generated module content is correct."""
        self.generator.generate_module(self.test_spec)
        
        # Test README content
        readme_content = (self.test_dir / "test_module" / "README.md").read_text()
        self.assertIn("Test Module", readme_content)
        self.assertIn("Testing the module generator", readme_content)
        
        # Test pyproject.toml content
        pyproject_content = (self.test_dir / "test_module" / "pyproject.toml").read_text()
        self.assertIn("name = \"test_module\"", pyproject_content)
        self.assertIn("A test module for unit testing", pyproject_content)

    def test_error_handling(self):
        """Test error handling during module generation."""
        # Test with invalid spec
        with patch.object(self.generator, '_generate_main', side_effect=Exception("Test error")):
            result = self.generator.generate_module(self.test_spec)
            self.assertEqual(result["status"], "error")
            self.assertIn("Test error", result["error"])


if __name__ == "__main__":
    unittest.main()
