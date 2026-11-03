from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stderr.write("This command is allowed only in dev environment",
                              style_func=self.style.ERROR)

        data = {
            "email": "test@localhost.com",
            "password": "Dev@123.",
            "name": "Adhithyan",
            "company_name": "tandoradev",
            "website": "https://tandora.co",
            "changelog_terminology": "test",
            "use_case": "c",
        }

        call_command('create_company',
                     f'--email={data["email"]}',
                     f'--name={data["name"]}',
                     f'--password={data["password"]}',
                     f'--company_name={data["company_name"]}',
                     f'--website={data["website"]}',
                     f'--changelog_terminology={data["changelog_terminology"]}',
                     f'--use_case={data["use_case"]}',
                     )
