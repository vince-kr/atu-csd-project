# Speak To Data

*your personal homesteading assistant*

![GHA workflow](https://github.com/github/docs/actions/workflows/pipeline.yml/badge.svg)

## Minimum viable product

This project verifies that the basic principles of the application are viable.
To that end, it will contain:

- Sample data representing typical events recorded over a year of keeping a
  homestead
- A simple Flask app that defines a single route, supporting GET and POST
- An index page which contains:
  - An input field for the user's query
  - Space underneath the input field for the response from HuggingFace

The application should:

- Accept queries from the user
- Call the deployed HuggingFace model with the query + sample data
- Present the response to the user

For now the page will not involve any JavaScript. The page will simply use a
POST request as a signal to query HuggingFace, and call its own GET routine
after a response from HuggingFace is received, reloading the page in the user's
browser.

## Technology

The application will use HuggingFace Transformers language bindings to interact
with the appropriate deployed model. This will most likely be Google TaPas with
the large dataset, but may change depending on experiments.

Local file `basic-qa.py` contains an example from HuggingFace's [page on the
TaPas model](https://huggingface.co/docs/transformers/model_doc/tapas). This
page has instructions for fine-tuning the model in case that's something I want
to look into at some point.

## Data shape

The TaPas model is powerful when it comes to reading data from tables, but it's
not great when the table in question represents a series of events rather than
a collection of "static" data. Since the data as recorded by a user is a series
of events, we need some extra steps in order to transform (hehe) the records of
events into a table with data for the period in question.

This is a task for NLP! But since it looks like fairly *straightforward* NLP,
I'm going to try implementing it myself instead of using yet another (slow)
deployed model for this.
