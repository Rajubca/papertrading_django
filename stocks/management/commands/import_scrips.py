import csv
import logging
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from stocks.models import Stock

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.FileHandler("import_scrips.log")  # log file in project root
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# python manage.py import_scrips "C:\Users\Admin\Downloads\ScripMaster.csv"

class Command(BaseCommand):
    help = "Import stocks from ScripMaster CSV into Stock model"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the ScripMaster CSV file")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        imported, updated, skipped = 0, 0, 0

        try:
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    trading_symbol = row.get("tradingSymbol")
                    if not trading_symbol:
                        skipped += 1
                        continue

                    try:
                        expiry_val = None
                        if row.get("expiryDate"):
                            try:
                                expiry_val = datetime.strptime(row["expiryDate"], "%Y-%m-%d").date()
                            except ValueError:
                                expiry_val = None  # ignore bad dates

                        obj, created = Stock.objects.update_or_create(
                            trading_symbol=trading_symbol,
                            defaults={
                                "name": row.get("name"),
                                "exchange": row.get("exchange"),
                                "isin": row.get("isin") or row.get("symbolCode"),
                                "instrument": row.get("instrument"),
                                "last_price": Decimal(row["lastPrice"]) if row.get("lastPrice") else None,
                                "expiry": expiry_val,
                                "strike_price": Decimal(row["strikePrice"]) if row.get("strikePrice") else None,
                                "option_type": row.get("optionType"),
                                "lotsize": int(row.get("lotSize")) if row.get("lotSize") else 1,
                            }
                        )
                        if created:
                            imported += 1
                        else:
                            updated += 1

                    except Exception as row_err:
                        skipped += 1
                        logger.error(f"Row skipped ({trading_symbol}): {row_err}")

            msg = f"Imported: {imported}, Updated: {updated}, Skipped: {skipped}"
            self.stdout.write(self.style.SUCCESS(msg))
            logger.info(msg)

        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
