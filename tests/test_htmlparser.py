# python3 -m tests.htmlparser_test

import sys
import json
import unittest

sys.path.append('../htmlparser')
from src.htmlparser.core import HTMLCourseParser

class HTMLParserTests(unittest.TestCase):
    def test_parse_courses(self):
        parser = HTMLCourseParser()

        with open('tests/data/courses.html', 'r') as f:
            for line in f:
                parser.feed(line)

        parser.close()
        courses = parser.get_course_dict()

        file = open('tests/data/results.json')
        courses_fixture = json.load(file)
        file.close()
        self.assertEqual(courses, courses_fixture)

    def test_parse_mapping(self):
        parser = HTMLCourseParser()

        with open('tests/data/courses.html', 'r') as f:
            for line in f:
                parser.feed(line)

        parser.close()
        courses = parser.get_course_mapping()

        file = open('tests/data/course_mapping.json')
        mapping_fixture = json.load(file)
        file.close()
        self.assertEqual(courses, mapping_fixture)
    
if __name__ == "__main__":
    unittest.main()
    