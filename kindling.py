#!/usr/bin/env python2
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
import email.utils as mail_util
import requests
import paperjam_mail as fetch


CONFIG_FILE = "conf.json"

def load_settings(filename):
    return fetch.load_settings(filename)

def save_settings(config, filename):
    fetch.save_settings(config, filename)

def fetch_emails(config):
    print "Fetching emails..."
    return fetch.fetch_emails(config)

def find_new_emails(config, emails):
    print "Figuring out which emails are new..."
    new_emails = fetch.find_new_emails(config, emails)
    print "Found {}.".format(len(new_emails))
    return new_emails

def get_valid_attachments(email):
    return fetch.get_valid_attachments(email)

def append_new_emails(config, processed):
    fetch.append_new_emails(config, processed)

def send_mail(book_list):
    print "Sending mail with {} attachment(s) to kindle...".format(len(book_list))

    smtp_conf = config["smtp"]
    msg = MIMEMultipart()
    msg['Subject'] = " "
    msg['From'] = smtp_conf["user"]
    msg['To'] = smtp_conf["kindle"]

    for name in book_list:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(name + ".mobi", "rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{}.mobi"'.format(name))
        msg.attach(part)

    server = smtplib.SMTP(smtp_conf["server"])
    server.starttls()
    server.login(smtp_conf["user"], smtp_conf["pass"])
    server.sendmail(msg["From"], msg["To"], msg.as_string())

def save_gutenberg_book(book_number):
    if book_number not in config["downloaded_books"]:
        url = "http://www.gutenberg.org/ebooks/{}.kindle.noimages".format(book_number)
        res = requests.get(url, stream=True)

        with open(book_number + ".mobi", 'wb') as fd:
            for chunk in res.iter_content(1024):
                fd.write(chunk)
        # remember that we downloaded this book
        config["downloaded_books"].append(book_number)

def process_link(link):
    return link.split("/ebooks/")[-1].split(".")[0]

def get_book_numbers(email):
    # i could replace this with a regex, but no
    numbers = [process_link(link) for link in email.split("\n") if
            link.startswith("http://www.gutenberg.org") or
            link.startswith("https://www.gutenberg.org")]
    return numbers

def extract_books(emails):
    book_numbers = set()
    for _, mail in emails:
        senders = mail_util.getaddresses(mail.get_all('from', []))
        sender_addresses = [mailaddr for name, mailaddr in senders]
        valids = [(m in config['sender_whitelist']) for m in sender_addresses]
        # a naive check, only continue if the sender was in the whitelist
        if not any(valids):
            continue
        email_body = get_valid_attachments(email)
        if email_body:
            # |= is the union operator, and apparently faster than set.add!
            book_numbers |= set(get_book_numbers(email_body[0]))
    return book_numbers

def save_and_send_books(books):
    if books:
        print "Downloading & saving {} to disk...".format(
                ", ".join([str(book) + ".mobi" for book in books]))
        for book in books:
            save_gutenberg_book(book)
        # send an email to my kindle with the .mobi files as attachments
        send_mail(books)
    else:
        print "No new books to download."

if __name__ == "__main__": 
    config = load_settings(CONFIG_FILE)
    emails = fetch_emails(config)
    new_emails = find_new_emails(config, emails)
    append_new_emails(config, [digest for digest, email in new_emails])
    book_numbers = extract_books(new_emails)
    new_books = book_numbers - set(config["downloaded_books"])
    # download, save & send all the new books
    save_and_send_books(new_books)
    # remember all the emails & books we've processed
    save_settings(config, CONFIG_FILE)
