
# to set up host email:

* Go to [Google AppPasswords](https://myaccount.google.com/apppasswords)
* Select App: Mail, Device: Other (Custom name) → e.g. DevWorks Mail.
* Google will generate a 16-character app password (looks like abcd efgh ijkl mnop).
* Replace your EMAIL_HOST_PASSWORD in settings.py with that app password

*dont forget to set `EMAIL_HOST_USER` to the email address of the password created and the following configurations*
```python
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```


