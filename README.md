# MONSTER

## Spidering

- Find interactions that produce forms
- Find all forms on a page
- __(?)__ Save some kind of state

## Attacking

- XSS
- SQLi

## Removing client-side validation

### General

- Remove:
    - "maxlength" attrib
    - "disabled" attrib
    - "max" attrib
    - "min" attrib
    - "pattern" attrib
    - "required" attrib
    - "steps" attrib
- Replace non-text "type" attrib to text
    - email
    - url
    - number
- Add "novalidate" attrib

### Bootstrap Validator

- Replace "type" to "text"
    - email
    - url
    - number
- Remove
    - "required" attrib
    - "data-match" attrib
    - "data-minlength" attrib
    - "data-remote" attrib
    - "pattern" attrib
- "data-html" attrib = true = YEEEEEEEEEEEEEEE
- look for calls to (HTML element).validator()
