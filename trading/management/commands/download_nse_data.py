# trading/management/commands/download_nse_data.py
import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Download NSE index data (NIFTY 50 and F&O stocks)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--index',
            type=str,
            choices=['nifty50', 'fno', 'all'],
            default='all',
            help='Which index to download (nifty50, fno, all)'
        )

    def download_csv(self, index_name, save_path):
        """
        Downloads index data as CSV from NSE
        """
        url = (
            "https://www.nseindia.com/api/equity-stockIndices"
            f"?csv=true&index={index_name.replace(' ', '%20').replace('&', '%26')}"
            "&selectValFormat=crores"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/market-data/live-equity-market",
        }

        try:
            with requests.Session() as session:
                session.get("https://www.nseindia.com/market-data/live-equity-market", headers=headers)
                response = session.get(url, headers=headers)
                response.raise_for_status()

                # Create data directory if it doesn't exist
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                with open(save_path, "wb") as f:
                    f.write(response.content)

            self.stdout.write(self.style.SUCCESS(f"{index_name} data saved to {save_path}"))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to download {index_name}: {str(e)}"))
            return False

    def handle(self, *args, **options):
        data_dir = os.path.join(settings.BASE_DIR, 'data', 'nse')

        indices = []
        if options['index'] in ['nifty50', 'all']:
            indices.append(('NIFTY 50', os.path.join(data_dir, 'nifty50.csv')))
        if options['index'] in ['fno', 'all']:
            indices.append(('SECURITIES IN F&O', os.path.join(data_dir, 'securities_fo.csv')))

        for index_name, save_path in indices:
            self.download_csv(index_name, save_path)