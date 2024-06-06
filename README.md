# Synchropoem
## Video Demo: https://www.youtube.com/watch?v=BBJSG2GF6t4
## Description 
Synchropoem is an experimental web application designed to explore the concept of interconnectedness and synchronicity through collaborative poetry. Participants contribute lines following specific formats, which are then combined randomly to form poems. If you encounter a poem that you resonate with, maybe synchronicity occurred, or maybe it was just coincidence :) The project leverages Flask for the backend, SQLite for the database, and various Python libraries for handling security, session management, and more. The project comes with 300 lines generated by GPT and an account created for GPT (gpt/1234).

## Table of Contents
#### Features
#### Setup and Installation
#### Usage
#### Files Description
#### Acknowledgements

## Features
- **User Registration and Authentication:** Secure user registration and login with hashed passwords.
- **Tooltip:** Provides information on website and functionalities.
- **Poetry Submission:** Users can submit lines in specified formats.
- **Random Poem Generation:** Randomly combines lines to create meaningful poems.
- **Like System:** Users can like poems and see the total count of likes.
- **Customization:** Users can select specific lines to ensure their contribution appears in a poem.
- **Notepad:** Users can view and manage their submitted lines.
- **Syncs:** Users can view the poems that they have liked.

## Setup and Installation

Clone the repository:
`git clone git@github.com:sVeritasium/synchropoem.git`

Run the application:
`flask run`

## Usage
- **Home Page:** View the randomly generated poem.
- **Register:** Create a new user account.
- **Login:** Log into an existing user account.
- **Submit** a Line: Submit a line following the specified format.
- **Customize Poem:** Choose specific lines to include in the poem.
- **Like Poems:** Like a poem and view the like count.
- **Notepad:** Manage your submitted lines.
- **Syncs:** View the poems you have liked.

## File Description

### Routes via app.py
- **/:** Main page displaying a poem.
- **/register:** Registration page for new users.
- **/login:** Login page for existing users.
- **/logout:** Logout route to end user sessions.
- **/entry:** POST route for submitting a new line.
- **/customize:** GET route for fetching user-specific data to customize poems.
- **/get_entries:** GET route for fetching lines from the database.
- **/like:** POST route for liking/unliking poems.
- **/notepad:** Page for viewing and managing user's lines.
- **/syncs:** Page for viewing liked poems.

### Helper Functions via helpers.py
- **login_required:** Decorator to ensure routes are accessible only to logged-in users.
- **validate_entry:** Validates the format of the submitted line.
- **transform_line:** Transforms the line to ensure consistency in formatting.
- **check_liked:** Checks if a user has liked a particular poem.
- **random_format:** Formats lines randomly to create a poem.

### Templates & CSS & JavaScript
- **index.html:** Main template displaying the poem and submission form.
- **register.html:** Template for user registration.
- **login.html:** Template for user login.
- **notepad.html:** Template for managing submitted lines.
- **syncs.html:** Template for viewing liked poems.
- **styles.css:** Styling for the pages
- **fetchLines:** Fetches lines from the server to display in the poem.
- **updateLineContent:** Updates the content of lines with animation.
- **updateLikeButton:** Updates the like button based on the like status.
- **setupFetchInterval:** Sets up an interval to periodically fetch lines.
- **setupCustomizeModal:** Sets up the customization modal for selecting lines.
- **setupLikeButton:** Sets up the like button functionality.

### Database via database.db
**SQL Schemas:**

CREATE TABLE users ( <BR>
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,<BR>
username TEXT NOT NULL,<BR>
hash TEXT NOT NULL,<BR>
date DATETIME NOT NULL<BR>
);<BR>
<BR>
CREATE TABLE lines (<BR>
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,<BR>
user_id INT NOT NULL,<BR>
line TEXT NOT NULL,<BR>
date DATETIME NOT NULL,<BR>
FOREIGN KEY (user_id) REFERENCES users(id)<BR>
);<BR>

CREATE TABLE likes (<BR>
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,<BR>
user_id INT NOT NULL,<BR>
poem_type TEXT NOT NULL,<BR>
line1_id INT NOT NULL,<BR>
line1 TEXT NOT NULL,<BR>
line2_id INT NOT NULL,<BR>
line2 TEXT NOT NULL,<BR>
line3_id INT NOT NULL,<BR>
line3 TEXT NOT NULL,<BR>
date DATETIME NOT NULL,<BR>
FOREIGN KEY (user_id) REFERENCES users(id),<BR>
FOREIGN KEY (line1_id) REFERENCES lines(id),<BR>
FOREIGN KEY (line2_id) REFERENCES lines(id),<BR>
FOREIGN KEY (line3_id) REFERENCES lines(id)<BR>
);<BR>

## Acknowledgements
CS50 course for providing the foundational knowledge and resources.
All the various articles and threads that were found on google.
GPT for explanations and assistance with coding. 
