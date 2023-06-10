# send2kindle
Bot for sending (converted) files to Amazon Kindle.

Bot uses fb2c and kindlegen to convert FB2 files to EPUB
Download them from https://github.com/rupor-github/fb2converter/releases and paste them into the bot directory before launching

With this bot, users can perform the following operations:

Command /start: Used to initialize the bot. When this command is called, the bot will send a welcome message and instructions on how to use the bot.

Command /email_add: Allows the user to add their email address to receive files. 
After entering the command in the format /email_add user@example.com, the bot will save the address and allow the user to send files or file links to receive them on their Kindle email.

Command /email_remove: Allows the user to remove all previously saved email addresses. After calling this command, all addresses will be deleted from the system.

Sending file links: Users can send the bot a link to a file for downloading and sending to their Kindle email. 
The bot will download the file from the provided link, check its format, and send it to the specified email address.

Sending documents: Users can send the bot a document (e.g., .doc, .pdf, .epub) to be sent to their Kindle email. 
The bot will download the document, check its format, perform necessary conversions (if required), and send it to the specified email address.

Other commands: If the user is an administrator, they can execute special commands such as running a system command, restarting the bot, or sending a file to Telegram.

In general, the bot provides users with the ability to send various types of files (links or documents) to receive them on their Kindle email after necessary checks and conversions. 
Additionally, the bot supports administrative functions for executing specific actions on the server, accessible only to the administrator.
