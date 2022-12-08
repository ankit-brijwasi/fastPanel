# fastPanel
A Django inspired admin panel for FARM stack developers, to make there development life easy!

# System requirements
Due to the limited support of the uvloop package in windows, the server might not start, to fix this, use the server in WSL

# Run the server
1. Activate your virtualenv
2. Install all the dependencies using, `pip install -r requirements.txt`
3. Add a file called `.env`  in the root with the following data
```bash
DB_HOST=dev-cluster.xxq5ptb.mongodb.net
DB_USER=dev
DB_PASSWORD=C0mtGefNUcTwDPkf
DB_NAME=devduels
```
4. Run the server using-
```bash
$ uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```