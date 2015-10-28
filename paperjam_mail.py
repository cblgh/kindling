#!/usr/bin/env python2

# Copyright (c) 2014, 2015, Linus Karlsson
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

# A modified version of the paperjam_mail util of
# https://github.com/zozs/paperjam/
import json
import poplib
import email.parser
import email.utils
import hashlib
import poplib


CONTENT_TYPES = ["text/plain"]

def load_settings(filename):
    """Load settings from JSON and returns config object."""
    with open(filename) as f:
        config = json.load(f)
        return config


def save_settings(config, filename):
    """Save settings to JSON."""
    print "Saving config..."
    with open(filename, "w") as f:
        json.dump(config, f, indent=2)


def fetch_emails(config):
    """Retrieves the emails from a POP server and returns them."""
    pop_conf = config["pop"]
    pop_conn = poplib.POP3_SSL(pop_conf["host"], pop_conf["port"])
    pop_conn.user(pop_conf["user"])
    pop_conn.pass_(pop_conf["pass"])

    # Get messages from server
    messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]
    messages = ["\n".join(msg[1]) for msg in messages]
    messages = [email.parser.Parser().parsestr(msg) for msg in messages]
    
    pop_conn.quit()
    return messages


def find_new_emails(config, emails):
    """Walks through e-mails, hashes them, and checks whether such a hash
    already exists in the config file. Only return new ones."""
    #digest_message = ((hashlib.sha256(m.as_bytes()).hexdigest(), m) for m in emails) #Python 3
    digest_message = ((hashlib.sha256(m.as_string()).hexdigest(), m) for m in emails)
    return [(d, m) for d, m in digest_message if d not in config["mail_hashes"]]


def get_valid_attachments(email):
    """Get all valid attachments of a message through recursion."""
    if email.is_multipart():
        attachments = []
        for p in email.get_payload():
            attachments.extend(get_valid_attachments(p))
        return attachments
    else:
        # Check content type.
        if email.get_content_type() in CONTENT_TYPES:
            # Valid content-type.
            return [email.get_payload(decode=True)]
        else:
            return []


def append_new_emails(config, processed):
    """Appends all hashes in processed to the config."""
    config["mail_hashes"].extend(processed)
