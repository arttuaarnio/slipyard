# ledger

A small personal-finance ledger on the command line. Transactions live in one JSON file. Amounts are exact decimals: negative is money spent, positive is income.

```
python3 -m ledger add 2024-03-02 -4.50 food --note coffee
python3 -m ledger add 2024-03-01 2000 salary
python3 -m ledger list
python3 -m ledger balance
python3 -m ledger import bank.csv
```

Use `--file PATH` to pick the ledger file (default `ledger.json`). Bank CSV exports have the columns `date,amount,category,note`.

Run the tests with `python3 -m unittest`.
