# TicTacTore With Flask + HTMX

----------
##  🎮 Project Overview
----------

This is a small project which allows users to play tictactoe on the web against the Computer or against a friend (locally).
You can earn points towards your placement on the leaderboard for each win or draw . All your stats are tracked on your profile too.
A working demo can be found at: https://tictactoe-htmx.onrender.com

NB: The website takes some time to load using render.


## 🧰 **Requirements**
----------

You can install all the requirements by running the following command from the main project directory:
    pip install -r requirements.txt

## 🟢 Quick Start
----------

 **After installing** [**requirements**]

First, you need to set up your environment variables in your .env file. 
An example is shown below.

    SECRET_KEY=123
    DB_URL=sqlite:///tictactoe-htmx.db
    UPLOAD_FOLDER=uploads # your path to store user images on the server

From the main project directory run:

     flask run

