# from __future__ import print_function
import re
import pickle
import os
import yaml
import argparse
import pprint


def clear_the_screen(number_of_empty_lines=100):
    print("\n" * number_of_empty_lines)


class StockRegister:
    def __init__(self, soldItemQuantities, soldItemRevenues, currencyCode):
        self.soldItemQuantities = soldItemQuantities    # Dictionary with item code and number of sold items
        self.soldItemRevenues = soldItemRevenues    # Dictionary with item code and item revenue
        self.currencyCode = currencyCode

    def show(self, products, itemsForSale):
        for itemCode, quantity in self.soldItemQuantities.items():
            print("[{itemCode:.^6}] {itemName:20} {itemQuantity:4} stuks ... {currencyCode} {itemRevenue:7.2f}".format(
                itemCode=itemsForSale[itemCode].code,
                itemName=itemsForSale[itemCode].name,
                itemQuantity=quantity,
                currencyCode=self.currencyCode,
                itemRevenue=self.soldItemRevenues[itemCode]
            ))


class CashRegister:
    def __init__(self, cash, turnover, transactions, currencyCode):
        self.cash = cash
        self.turnover = turnover
        self.transactions = transactions
        self.currencyCode = currencyCode

    def show(self):
        print("{prefix:20} {cash:7.2f}".format(
            prefix="Cash ({currencyCode})".format(currencyCode=self.currencyCode),
            cash=self.cash))
        print("{prefix:20} {turnover:7.2f}".format(
            prefix="Omzet ({currencyCode})".format(currencyCode=self.currencyCode),
            turnover=self.turnover))
        print("{prefix:20} {transactions:4}".format(
            prefix="Transacties",
            transactions=self.transactions))


class Item:
    def __init__(self, code, name, unitprice, order):
        self.code= code
        self.name = name
        self.unitPrice = unitprice
        self.order = order  # Future use: print sorted list

    def __str__(self):
        return 'Code: {} - Name: {} - Unit price: {}'.format(self.code, self.name, self.unitPrice)


class ShoppingCart():
    def __init__(self, currencyCode):
        self.itemQuantities = {}   # Dictionary of product objects and itemQuantities in the shopping cart
        self.numberOfItems = 0     # Number of itemQuantities in the shopping cart
        self.amount = 0.00         # Amount (Euro's, ...) of the shopping cart
        self.cash = 0.00           # Amount (Euro's, ...) received from customer
        self.currencyCode = currencyCode

    def show(self):
        print()
        print()
        for item, quantity in self.itemQuantities.items():
            if quantity != 0:
                print("{itemName:<30} {itemQuantity:4} x {currencyCode} {unitPrice:3.2f} = {currencyCode} {totalItemPrice:>6.2f}"\
                .format(itemName=item.name,
                        itemQuantity=quantity,
                        unitPrice=item.unitPrice,
                        totalItemPrice=quantity * item.unitPrice,
                        currencyCode=self.currencyCode))
        if self.amount != 0:
            print()
            print("Totaal {numberOfItems:>28} item(s)      {currencyCode} {amount:6.2f}".format(numberOfItems=self.numberOfItems,
                                                                                                amount=self.amount,
                                                                                                currencyCode=self.currencyCode))
        if self.cash != 0:
            print()
            print()
            print("{cashString:>46}   {currencyCode} {cash:6.2f}".format(cashString="Cash",
                                                                         cash=self.cash,
                                                                         currencyCode=self.currencyCode))
            print()
            print("{changeString:>46}   {currencyCode} {change:6.2f}".format(changeString="Terug",
                                                                             change=self.cash - self.amount,
                                                                             currencyCode=self.currencyCode))

    def addItem(self, item, quantity=1):
        self.numberOfItems += quantity
        self.amount += quantity * item.unitPrice
        if item in self.itemQuantities:
            self.itemQuantities[item] += quantity
        else:
            self.itemQuantities[item] = quantity

    def addCash(self, amount):
        self.cash += amount

    def removeCash(self, amount):
        self.cash -= amount

    def setCash(self, amount):
        self.cash = amount

    def removeItem(self, item, quantity=1):
        if quantity != 0:
            if item in self.itemQuantities:
                if self.itemQuantities[item] > quantity:
                    print("Removing less than total.")
                    self.itemQuantities[item] -= quantity
                    self.numberOfItems -= quantity
                    self.amount -= quantity * item.unitPrice
                elif self.itemQuantities[item] == quantity:
                    print("Removing total.")
                    del self.itemQuantities[item]
                    self.numberOfItems -= quantity
                    self.amount -= quantity * item.unitPrice
                elif self.itemQuantities[item] < quantity:
                    print("Receiving returned goods.")
                    self.itemQuantities[item] -= quantity
                    self.numberOfItems -= quantity
                    self.amount -= quantity * item.unitPrice
            else:
                print("Receiving returned goods (item is not present in shopping cart).")
                self.itemQuantities[item] = -quantity
                self.numberOfItems -= quantity
                self.amount -= quantity * item.unitPrice

    def setItem(self, item, quantity=0):
        if item not in self.itemQuantities:
            self.addItem(item, quantity)
        else:
            self.removeItem(item, self.itemQuantities[item])
            self.addItem(item, quantity)

    def closeTransaction(self, cashRegister, stockRegister, currencyCode):
        cashRegister.cash += self.amount
        cashRegister.turnover += self.amount
        if self.amount != 0:
            cashRegister.transactions += 1
        for item, quantity in self.itemQuantities.items():
            stockRegister.soldItemQuantities[item.code] += quantity
            print(stockRegister)
            stockRegister.soldItemRevenues[item.code] += quantity * item.unitPrice
        pickle.dump(cashRegister, open("cashRegister.p", "wb"), protocol=2)
        pickle.dump(stockRegister, open("stockRegister.p", "wb"), protocol=2)
        self.__init__(currencyCode)
        return cashRegister, stockRegister


def main(configFileName, args):
    pp = pprint.PrettyPrinter(indent=4)
    try:
        with open(os.path.join(args.config_folder, configFileName), "r") as yamlFile:
            config = yaml.load(yamlFile)
    except Exception as inst:
        print("Failed to open or interpret config file: {}".format(inst))
        exit()  # Exit if the config file can not be read
    else:
        print("Config file {} interpreted.".format(yamlFile))

    itemsForSale = {}  # Dict of productCode and product object
    soldItemQuantities = {}  # Dict of productCode and number of sold items
    soldItemRevenues = {} # Dict of productCode and revenue for that item
    for product in config['products']:
        if product['code'] in itemsForSale:
            print("ERROR: Multiple products with code '{}' detected in config file '{}'.".format(product['code'], configFileName))
            exit('DUPLICATE PRODUCT CODE')
        itemsForSale[product['code']] = Item(code=product['code'],
                                             name=product['name'],
                                             unitprice=product['price'],
                                             order=product['order'])
        soldItemQuantities[product['code']] = 0
        soldItemRevenues[product['code']] = 0

    shoppingCart = ShoppingCart(config['currencyCode'])

    cashRegister = CashRegister(config['initial']['cash'], 0, 0, config['currencyCode'])
    try:
        cashRegister = pickle.load(open("cashRegister.p", "rb"))
    except IOError as e:
        print("I/O error ({0}): {1}".format(e.errno, e.strerror))

    stockRegister = StockRegister(soldItemQuantities, soldItemRevenues, config['currencyCode'])
    try:
        stockRegister = pickle.load(open("stockRegister.p", "rb"))
    except IOError as e:
        print("I/O error ({0}): {1}".format(e.errno, e.strerror))

    regex = re.compile(r'^\s*(?P<item_operation>[-+=]{0,1})(?P<item_quantity>\d{0,})(?P<item_code>[a-z]+)\s*$')
    # More info on regex: https://docs.python.org/2/library/re.html

    while True:
        clear_the_screen()
        cashRegister.show()
        stockRegister.show(config['products'], itemsForSale)
        shoppingCart.show()
        requested_items_string = input("\n--> ")
        requested_items_list = requested_items_string.lower().split(" ")
        if requested_items_list == ['qq']:
            print("QUIT")
            break
        if requested_items_list == ['rr']:
            print("RESET")
            shoppingCart.__init__(config['currencyCode'])
        elif requested_items_list == ['nn']:
            print("Next customer!")
            cashRegister, stockRegister = shoppingCart.closeTransaction(cashRegister, stockRegister, config['currencyCode'])
        else:
            for operation_amount_and_item in requested_items_list:
                result_search = regex.search(operation_amount_and_item)
                if result_search is not None:
                    product_operation = result_search.group('item_operation')
                    product_quantity = result_search.group('item_quantity')
                    product_code = result_search.group('item_code')
                    print(product_operation, product_quantity, product_code)
                    if product_code == "eu":
                        product_code = "cash"
                    if not product_quantity:
                        product_quantity = 1
                    if not product_operation:
                        product_operation = "+"
                    if product_code in itemsForSale:
                        if product_operation == "+":
                            shoppingCart.addItem(itemsForSale[product_code], int(product_quantity))
                        elif product_operation == "-":
                            shoppingCart.removeItem(itemsForSale[product_code], int(product_quantity))
                        elif product_operation == "=":
                            shoppingCart.setItem(itemsForSale[product_code], int(product_quantity))
                    elif product_code == "cash" and product_operation == "+":
                        shoppingCart.addCash(int(product_quantity))
                    elif product_code == "cash" and product_operation == "-":
                        shoppingCart.removeCash(int(product_quantity))
                    elif product_code == "cash" and product_operation == "=":
                        shoppingCart.setCash(int(product_quantity))
                    else:
                        print("Product with code {} is not known.".format(product_code))

config_file = "mopos.yaml"

parser = argparse.ArgumentParser(description='MyOwnPointOfSales: keeping track of cash and goods.')
parser.add_argument('--config-folder',
                    default=".",
                    help='Config folder, in which the config file is located')
args = parser.parse_args()

if __name__ == "__main__":
    main(config_file, args)
