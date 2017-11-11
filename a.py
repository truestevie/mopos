import re
import pickle
import os
import yaml
import argparse
from pprint import pprint

config_file = "a.yaml"

class ItemDescription():
    def __init__(self, code, name, unitPrice, printOrder):
        self.code= code
        self.name = name
        self.unitPrice = unitPrice
        self.printOrder = printOrder  # Future use: print sorted list

    def __str__(self):
        return 'Code: {} - Name: {} - Unit price: {} - Order: {}'\
            .format(self.code, self.name, self.unitPrice, self.printOrder)


class ShoppingBasket():
    def __init__(self, currencyCode="EUR"):
        self.itemQuantities = {}    # Dictionary of product objects and itemQuantities in the shopping cart
        self.numberOfItems = 0      # Number of items in the shopping cart
        self.cashTotal = 0.00           # Total amount (Euro's, ...) of the shopping cart
        self.cashReceived = 0.00    # Amount (Euro's, ...) received from customer
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
        if self.cashTotal != 0:
            print()
            print("Totaal {numberOfItems:>28} item(s)      {currencyCode} {amount:6.2f}".format(numberOfItems=self.numberOfItems,
                                                                                                amount=self.cashTotal,
                                                                                                currencyCode=self.currencyCode))
        if self.cashReceived != 0:
            if self.cashReceived >= self.cashTotal:
                cashStringWithCheck = "Ontvangen"
            else:
                cashStringWithCheck = "Ontvangen (ONTOEREIKEND)"
            print()
            print()
            print("{cashString:>46}   {currencyCode} {cash:6.2f}".format(cashString=cashStringWithCheck,
                                                                         cash=self.cashReceived,
                                                                         currencyCode=self.currencyCode))
            print()
            print("{changeString:>46}   {currencyCode} {change:6.2f}".format(changeString="Terug",
                                                                             change=self.cashReceived - self.cashTotal,
                                                                             currencyCode=self.currencyCode))

    def addItem(self, itemObject, quantity=1):
        if quantity > 0:
            self.numberOfItems += quantity
            self.cashTotal += quantity * itemObject.unitPrice
            if itemObject in self.itemQuantities:
                self.itemQuantities[itemObject] += quantity
            else:
                self.itemQuantities[itemObject] = quantity
            print("Item '{}' added to shopping cart. New quantity = {}.".format(itemObject.name, self.itemQuantities[itemObject]))
        else:
            print("Number of items to be added should be larger than 0!")

    def addCash(self, amount):
        if amount > 0:
            self.cashReceived += amount
        else:
            print("Amount should be larger than 0!")

    def removeCash(self, amount):
        if amount > 0:
            if amount < self.cashReceived:
                self.cashReceived -= amount
            else:
                print("Unable to remove {currencyCode} {amount:.2f} from basket, "
                "it has only {currencyCode} {cashReceived:.2f} available.".format(
                    currencyCode=self.currencyCode,
                    amount=amount,
                    cashReceived=self.cashReceived))
        else:
            print("Amount should be larger than 0!")

    def setCash(self, amount):
        if amount > 0:
            self.cashReceived = amount
        else:
            print("Amount should be larger than 0!")


    def removeItem(self, itemObject, quantity=1):
        if quantity > 0:
            if itemObject in self.itemQuantities:
                if self.itemQuantities[itemObject] > quantity:
                    print("Removing less than total.")
                    self.itemQuantities[itemObject] -= quantity
                    self.numberOfItems -= quantity
                    self.cashTotal -= quantity * itemObject.unitPrice
                elif self.itemQuantities[itemObject] == quantity:
                    print("Removing total.")
                    del self.itemQuantities[itemObject]
                    self.numberOfItems -= quantity
                    self.cashTotal -= quantity * itemObject.unitPrice
                elif self.itemQuantities[itemObject] < quantity:
                    # Not possible with quantity > 0 check.
                    # Should we allow to receive return goods?
                    # To be included in other call...?
                    print("Receiving returned goods.")
                    self.itemQuantities[itemObject] -= quantity
                    self.numberOfItems -= quantity
                    self.cashTotal -= quantity * itemObject.unitPrice
            else:
                print("Receiving returned goods (item is not present in current shopping cart).")
                self.itemQuantities[itemObject] = -quantity
                self.numberOfItems -= quantity
                self.cashTotal -= quantity * itemObject.unitPrice
        else:
            print("Number of items to be removed should be larger than 0!")


    def setItem(self, item, quantity=0):
        if item not in self.itemQuantities:
            self.addItem(item, quantity)
        else:
            self.removeItem(item, self.itemQuantities[item])
            self.addItem(item, quantity)

    def closeTransaction(self, cashRegister, stockRegister, currencyCode):
        # stockRegister.update(self)
        if self.cashTotal != 0:
            cashRegister.addTransaction(1)
            cashRegister.addCashAndRevenue(self.cashTotal)
        for item, quantity in self.itemQuantities.items():
            stockRegister.registerSoldItem(itemCode=item.code, itemUnitPrice=item.unitPrice, itemQuantity=quantity)
        pickle.dump(cashRegister, open("cashRegister.p", "wb"), protocol=2)
        pickle.dump(stockRegister, open("stockRegister.p", "wb"), protocol=2)
        return cashRegister, stockRegister


class CashRegister:
    def __init__(self, cash=0, revenue=0, transactions=0, currencyCode="EUR"):
        self.cash = cash
        self.revenue = revenue
        self.transactions = transactions
        self.currencyCode = currencyCode

    def show(self):
        print("{prefix:20} {cash:7.2f}".format(
            prefix="Cash ({currencyCode})".format(currencyCode=self.currencyCode),
            cash=self.cash))
        print("{prefix:20} {revenue:7.2f}".format(
            prefix="Omzet ({currencyCode})".format(currencyCode=self.currencyCode),
            revenue=self.revenue))
        print("{prefix:20} {transactions:4}".format(
            prefix="Transacties",
            transactions=self.transactions))

    def addTransaction(self, transactions=1):
        self.transactions += transactions
        print(self.transactions)

    def addCashAndRevenue(self, cash=0):
        self.cash += cash
        self.revenue += cash
        print(self.cash)



class StockRegister:
    def __init__(self, soldItemQuantities, soldItemRevenues, currencyCode="EUR"):
        self.soldItemQuantities = soldItemQuantities    # Dictionary with item code and number of sold items
        self.soldItemRevenues = soldItemRevenues    # Dictionary with item code and item revenue
        self.currencyCode = currencyCode

    def show(self, products, itemsForSale):
        for itemCode, quantity in self.soldItemQuantities.items():
            print("[{itemCode:.^6}] {itemName:20} {itemQuantity:4} stuks ... {currencyCode} {itemRevenue:7.2f} ... Real revenue {revenue}".format(
                itemCode=itemsForSale[itemCode].code,
                itemName=itemsForSale[itemCode].name,
                itemQuantity=quantity,
                currencyCode=self.currencyCode,
                itemRevenue=self.soldItemRevenues[itemCode],
                revenue=itemsForSale[itemCode].revenue
            ))

    def update(self, soldItemQuantities, soldItemRevenues):
        for itemCode, itemQuantity in soldItemQuantities:
            print(itemcode, itemQuantity)

    def registerSoldItem(self, itemCode, itemUnitPrice, itemQuantity):
        if itemCode in self.soldItemQuantities:
            self.soldItemQuantities[itemCode] += itemQuantity
        else:
            self.soldItemQuantities[itemCode] = itemQuantity
        if itemCode in self.soldItemRevenues:
            self.soldItemRevenues[itemCode] += itemQuantity * itemUnitPrice
        else:
            self.soldItemRevenues[itemCode] = itemQuantity * itemUnitPrice


parser = argparse.ArgumentParser(description='MyOwnPointOfSales: keeping track of cash and goods.')
parser.add_argument('--config-folder',
                    default=".",
                    help='Config folder, in which the config file is located')
args = parser.parse_args()


def main(configFile, args):
    try:
        with open(os.path.join(args.config_folder, configFile), "r") as yamlFile:
            config = yaml.load(yamlFile)
    except Exception as inst:
        print("Failed to open or interpret config file: {}".format(inst))
        exit()  # Exit if the config file can not be read
    else:
        print("Config file '{}' interpreted.".format(yamlFile.name))
        pprint(config)
    currencyCode = config['currencyCode']
    itemDescriptions = {}

    for product in config['products']:
        if product['code'] in itemDescriptions:
            print("ERROR: Multiple products with code '{}' detected in config file '{}'."
                  .format(product['code'], configFile))
            exit('DUPLICATE PRODUCT CODE')
        print("Defining product '{}'.".format(product['name']))
        itemDescriptions[product['code']] = ItemDescription(code=product['code'],
                                             name=product['name'],
                                             unitPrice=product['price'],
                                             printOrder=product['printOrder'])
        # soldItemQuantities[product['code']] = 0

    for code, item in itemDescriptions.items():
        print("{code} -- {item}".format(code=code, item=item))

    cashRegister = CashRegister(cash=config['initial']['cash'], currencyCode=currencyCode)
    try:
        cashRegister = pickle.load(open("cashRegister.p", "rb"))
    except IOError as e:
        print("I/O error ({0}): {1}".format(e.errno, e.strerror))

    soldItemQuantities = {}
    soldItemRevenues = {}
    stockRegister = StockRegister(soldItemQuantities, soldItemRevenues, config['currencyCode'])
    try:
        stockRegister = pickle.load(open("stockRegister.p", "rb"))
    except IOError as e:
        print("I/O error ({0}): {1}".format(e.errno, e.strerror))

    cashRegister.show()

    # print(itemDescriptions['iv'])
    shoppingBasket = ShoppingBasket(currencyCode)
    shoppingBasket.addItem(itemDescriptions['ik'], 10)
    shoppingBasket.addItem(itemDescriptions['iv'], 20)
    shoppingBasket.addItem(itemDescriptions['dk'], 30)
    shoppingBasket.addItem(itemDescriptions['db'], 40)
    shoppingBasket.addCash(200)
    shoppingBasket.addCash(200)
    # shoppingBasket.removeItem(itemDescriptions['ik'], 1)
    shoppingBasket.show()
    cashRegister, stockRegister = shoppingBasket.closeTransaction(
        cashRegister=cashRegister,
        stockRegister=stockRegister,
        currencyCode=currencyCode)
    print(cashRegister, stockRegister)
    cashRegister.show()

    # shoppingCart.removeCash("Aha")
    # shoppingCart.setCash("Aha")
    # shoppingCart.show()
    # shoppingCart.removeItem(itemDescriptions['db'], 2)


if __name__ == "__main__":
    main(config_file, args)