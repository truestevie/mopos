# mopos
My Own Point Of Sale

Command line based Point Of Sale program.
Supporting small scale sales of well defined items.

Originally written for Python 2.7.
Now updated to run on Python 3.6.3.

## Features
- Config file (YAML)
- Support return of goods (receive goods, handout money)

## On the to do list...
- Support acceptance of small donations (for those that don't want to receive their change money: "keep the change" button)
- Provide "number of remaining available items" indication.
- Support transfer of money to night vault (to reduce amount of money in active cash register)
- Provide a way to view previous transactions.
- Provide a way to add a text comment to a transaction.
- Use Bottle to build a web interface.

## Inspiration
- https://docs.python.org/3/howto/pyporting.html
- http://buildingskills.itmaybeahack.com/book/programming-2.6/html/p13_modules/p13_c03_decimal.html
