# Save this file as your_app_name/management/commands/populate_topics.py

import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# Import your models from the correct path.
# Assumes 'biilim' is your app name.
from biilim.learn.models import Topic, Section

User = get_user_model()


class Command(BaseCommand):
    """
    A management command to populate the database with sample topics and sections.
    This version does not use the Faker library.
    """

    help = 'Populates the database with sample Topic and Section data.'

    # Define a list of topic data to use
    TOPICS_DATA = [
        {"title": "Introduction to Python", "description": "Learn the fundamentals of Python programming, including syntax, data types, and control flow."},
        {"title": "Web Development Basics", "description": "An overview of core web technologies: HTML, CSS, and JavaScript. This topic covers the basic building blocks of any website."},
        {"title": "Database Design Fundamentals", "description": "Explore the principles of relational database design, including normalization, schema creation, and SQL queries."},
        {"title": "Machine Learning for Beginners", "description": "A gentle introduction to machine learning concepts, covering supervised and unsupervised learning models."},
        {"title": "Data Structures and Algorithms", "description": "Understand common data structures and algorithms, which are essential for efficient problem-solving."},
        {"title": "Object-Oriented Programming (OOP)", "description": "Dive into the core concepts of OOP: classes, objects, inheritance, and polymorphism."},
        {"title": "Network Protocols Explained", "description": "An easy-to-understand guide to essential network protocols like TCP/IP, HTTP, and DNS."},
        {"title": "Introduction to Cybersecurity", "description": "Learn about the basics of cybersecurity, including common threats, vulnerabilities, and prevention strategies."},
        {"title": "Software Project Management", "description": "Explore the principles and methodologies for managing software development projects, from Agile to Waterfall."},
        {"title": "Frontend Frameworks: A Comparison", "description": "A look at popular frontend frameworks like React, Vue, and Angular, and their respective pros and cons."}
    ]

    def handle(self, *args, **options):
        """
        The main logic for the command.
        """
        self.stdout.write(self.style.WARNING('Clearing existing Topic and Section data...'))
        Section.objects.all().delete()
        Topic.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # Try to get an existing user to assign as 'created_by'.
        # This is a good practice to avoid errors on non-nullable fields.
        try:
            first_user = User.objects.first()
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('No users found. "created_by" will be left null.'))
            first_user = None

        self.stdout.write(self.style.SUCCESS('Starting to create sample data...'))

        # Create topics from the predefined list
        for data in self.TOPICS_DATA:
            topic = Topic.objects.create(
                title=data['title'],
                description=data['description'],
                duration=random.randint(30, 180),  # Random duration
                created_by=first_user
            )
            self.stdout.write(self.style.SUCCESS(f'Created topic: {topic.title}'))

            # Create a random number of sections for each topic (between 3 and 7)
            num_sections = random.randint(3, 7)
            for j in range(num_sections):
                section_title = f'Section {j+1}: {topic.title} - '
                if j == 0:
                    section_title += 'Introduction'
                elif j == num_sections - 1:
                    section_title += 'Conclusion'
                else:
                    section_title += f'Key Concept {j}'

                Section.objects.create(
                    topic=topic,
                    title=section_title,
                    content=f'This is the content for {section_title}. It provides a detailed explanation of the concepts discussed in this section.',
                    index=j
                )
            self.stdout.write(f'  - Created {num_sections} sections for {topic.title}')

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with sample data.'))
