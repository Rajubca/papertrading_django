import csv
import logging
import requests
from io import StringIO
from django.core.management.base import BaseCommand
from stocks.models import Stock

logger = logging.getLogger(__name__)

# python manage.py import_scrips


class Command(BaseCommand):
    help = "Import or update scrips from StockNote ScripMaster.csv"

    def handle(self, *args, **kwargs):
        url = "https://developers.stocknote.com/doc/ScripMaster.csv"

        self.stdout.write(self.style.NOTICE(f"📥 Downloading scrips from {url}..."))

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            self.stderr.write(self.style.ERROR(f"❌ Error downloading CSV: {e}"))
            return

        csv_file = StringIO(response.text)
        reader = csv.DictReader(csv_file)

        count_new, count_updated = 0, 0

        for row in reader:
            try:
                trading_symbol = row.get("TradingSymbol") or row.get("trading_symbol")
                if not trading_symbol:
                    continue

                obj, created = Stock.objects.update_or_create(
                    trading_symbol=trading_symbol,
                    defaults={
                        "name": row.get("Name", ""),
                        "exchange": row.get("Exchange", ""),
                        "instrument": row.get("Instrument", ""),
                        "last_price": row.get("LastPrice") or 0,
                        "isin": row.get("ISIN", ""),
                    },
                )

                if created:
                    count_new += 1
                else:
                    count_updated += 1

            except Exception as e:
                logger.error(f"⚠️ Error processing {row}: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"✅ Import completed! {count_new} new, {count_updated} updated."
        ))
