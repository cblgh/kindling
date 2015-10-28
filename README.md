# kindling
A small python 2.7 script for sending books from [Project Gutenberg](https://www.gutenberg.org/) to your Kindle.


It works by downloading all the emails of the email address specified in the config. 
It then reads those emails for any Project Gutenberg links. If it finds any, it downloads the books they
correspond to and whisks them off to your kindle through [emailing it](http://www.amazon.com/gp/sendtokindle/email).

