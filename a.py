encoding: "UTF-8"

import pickle
import re
import os
import yaml
import argparse
import decimal

D = decimal.Decimal
cent = D('0.01')


class ItemDescription:
    def __init__(self, code, name, unit_price, print_order):
        self.code = code
        self.name = name
        self.unitPrice = D(unit_price)
        self.printOrder = print_order  # Future use: print sorted list

    def __str__(self):
        return 'Code: {} - Name: {} - Unit price: {} - Order: {}'\
            .format(self.code, self.name, self.unitPrice, self.printOrder)


class ShoppingBasket:
    def __init__(self, currency_code="EUR"):
        self.itemQuantities = {}     # Dictionary of product objects and itemQuantities in the shopping cart
        self.numberOfItems = 0       # Number of items in the shopping cart
        self.cashTotal = D(0.00)     # Total amount (Euro's, ...) of the shopping cart
        self.cashReceived = D(0.00)  # Amount (Euro's, ...) received from customer
        self.currencyCode = currency_code

    def show(self):
        print()
        print()
        for item, quantity in self.itemQuantities.items():
            if quantity != 0:
                print("{itemName:<30} {itemQuantity:4} x {currencyCode} {unitPrice:3.2f} = "
                      "{currencyCode} {totalItemPrice:>6.2f}".format(itemName=item.name,
                                                                     itemQuantity=quantity,
                                                                     unitPrice=item.unitPrice,
                                                                     totalItemPrice=quantity * item.unitPrice,
                                                                     currencyCode=self.currencyCode))
        if self.cashTotal != 0:
            print()
            print("Totaal {numberOfItems:>28} item(s)      {currencyCode} {amount:6.2f}"
                  .format(numberOfItems=self.numberOfItems, amount=self.cashTotal, currencyCode=self.currencyCode))
        if self.cashReceived != 0:
            if self.cashReceived >= self.cashTotal:
                cash_string_with_check = "Ontvangen"
            else:
                cash_string_with_check = "Ontvangen (ONTOEREIKEND)"
            print()
            print()
            print("{cashString:>46}   {currencyCode} {cash:6.2f}".format(cashString=cash_string_with_check,
                                                                         cash=self.cashReceived,
                                                                         currencyCode=self.currencyCode))
            print()
            print("{changeString:>46}   {currencyCode} {change:6.2f}".format(changeString="Terug",
                                                                             change=self.cashReceived - self.cashTotal,
                                                                             currencyCode=self.currencyCode))

    def add_item(self, item_object, quantity=1):
        if quantity > 0:
            self.numberOfItems += quantity
            self.cashTotal += quantity * item_object.unitPrice
            if item_object in self.itemQuantities:
                self.itemQuantities[item_object] += quantity
            else:
                self.itemQuantities[item_object] = quantity
            print("Item '{}' added to shopping basket. New quantity = {}."
                  .format(item_object.name, self.itemQuantities[item_object]))
        else:
            print("Number of items to be added should be larger than 0!")

    def add_cash(self, amount):
        if amount > 0:
            self.cashReceived += amount
        else:
            print("Amount should be larger than 0!")

    def remove_cash(self, amount):
        if amount > 0:
            if amount < self.cashReceived:
                self.cashReceived -= amount
            else:
                print("Unable to remove {currencyCode} {amount:.2f} from basket, it has only {currencyCode}"
                      " {cashReceived:.2f} available.".format(currencyCode=self.currencyCode,
                                                              amount=amount,
                                                              cashReceived=self.cashReceived))
        else:
            print("Amount should be larger than 0!")

    def set_cash(self, amount):
        if amount > 0:
            self.cashReceived = amount
        else:
            print("Amount should be larger than 0!")

    def remove_item(self, item_object, quantity=1):
        if quantity > 0:
            if item_object in self.itemQuantities:
                if self.itemQuantities[item_object] > quantity:
                    print("Removing less than total.")
                    self.itemQuantities[item_object] -= quantity
                    self.numberOfItems -= quantity
                    self.cashTotal -= quantity * item_object.unitPrice
                elif self.itemQuantities[item_object] == quantity:
                    print("Removing total.")
                    del self.itemQuantities[item_object]
                    self.numberOfItems -= quantity
                    self.cashTotal -= quantity * item_object.unitPrice
                elif self.itemQuantities[item_object] < quantity:
                    # Not possible with quantity > 0 check.
                    # Should we allow to receive return goods?
                    # To be included in other call...?
                    print("Receiving returned goods.")
                    self.itemQuantities[item_object] -= quantity
                    self.numberOfItems -= quantity
                    self.cashTotal -= quantity * item_object.unitPrice
            else:
                print("Receiving returned goods (item is not present in current shopping cart).")
                self.itemQuantities[item_object] = -quantity
                self.numberOfItems -= quantity
                self.cashTotal -= quantity * item_object.unitPrice
        else:
            print("Number of items to be removed should be larger than 0!")

    def set_item(self, item, quantity=0):
        if item not in self.itemQuantities:
            self.add_item(item, quantity)
        else:
            self.remove_item(item, self.itemQuantities[item])
            self.add_item(item, quantity)

    def close_transaction(self, cash_register, stock_register):
        if self.cashTotal != 0:
            cash_register.add_transaction(1)
            cash_register.add_cash_and_revenue(self.cashTotal)
            cash_register.save_data()
        for item, quantity in self.itemQuantities.items():
            stock_register.register_sold_item(item_code=item.code,
                                              item_unit_price=item.unitPrice,
                                              item_quantity=quantity)
        stock_register.save_data()
        self.__init__()
        return cash_register, stock_register


class CashRegister:
    def __init__(self, cash=0, revenue=0, transactions=0, currency_code="EUR",
                 storage_location="./cashRegister.pickle"):
        self.cash = D(cash)
        self.revenue = D(revenue)
        self.transactions = transactions
        self.currency_code = currency_code
        self.storage_location = storage_location

    def show_one_line(self):
        print("Cash: {currency_code} {cash} - Omzet: {currency_code} {revenue} - Transacties: "
              "{transactions}".format(cash=self.cash.quantize(cent),
                                           revenue=self.revenue.quantize(cent),
                                           currency_code = self.currency_code,
                                           transactions = self.transactions))

    def show(self):
        print("{prefix:20} {cash:7.2f}".format(
            prefix="Cash ({currencyCode})".format(currencyCode=self.currency_code),
            cash=self.cash))
        print("{prefix:20} {revenue:7.2f}".format(
            prefix="Omzet ({currencyCode})".format(currencyCode=self.currency_code),
            revenue=self.revenue))
        print("{prefix:20} {transactions:4}".format(
            prefix="Transacties",
            transactions=self.transactions))

    def add_transaction(self, transactions=1):
        self.transactions += transactions
        print(self.transactions)

    def add_cash_and_revenue(self, cash=0):
        self.cash += cash
        self.revenue += cash
        print(self.cash.quantize(cent, rounding=decimal.ROUND_DOWN))

    def save_data(self):
        pickle.dump(self, open(self.storage_location, "wb"), protocol=2)


class StockRegister:
    def __init__(self, sold_item_quantities, sold_item_revenues, currency_code="EUR",
                 storage_location="./stockRegister.pickle"):
        self.soldItemQuantities = sold_item_quantities    # Dictionary with item code and number of sold items
        self.soldItemRevenues = sold_item_revenues    # Dictionary with item code and item revenue
        self.currencyCode = currency_code
        self.storage_location = storage_location

    def show(self):
        for itemCode, quantity in self.soldItemQuantities.items():
            print(itemCode,
                  quantity,
                  self.soldItemRevenues[itemCode],
                  self.soldItemRevenues[itemCode].quantize(cent, rounding=decimal.ROUND_DOWN))

    def show_one_line(self, item_descriptions):
        separator = ""
        for item_code, quantity in self.soldItemQuantities.items():
            print("[{separator}{item_code}: {quantity} x € {unit_price} = € {revenue}".format(
                separator=separator,
                item_code=item_code,
                quantity=quantity,
                unit_price=item_descriptions[item_code].unitPrice.quantize(cent, rounding=decimal.ROUND_DOWN),
                revenue=self.soldItemRevenues[item_code].quantize(cent, rounding=decimal.ROUND_DOWN)
            ), end="] ")
            #separator = " - "

    def register_sold_item(self, item_code, item_unit_price, item_quantity):
        if item_code in self.soldItemQuantities:
            self.soldItemQuantities[item_code] += item_quantity
        else:
            self.soldItemQuantities[item_code] = item_quantity
        if item_code in self.soldItemRevenues:
            self.soldItemRevenues[item_code] += item_quantity * item_unit_price
        else:
            self.soldItemRevenues[item_code] = item_quantity * item_unit_price

    def save_data(self):
        pickle.dump(self, open(self.storage_location, "wb"), protocol=2)


def clear_the_screen(number_of_empty_lines=100):
    print("\n" * number_of_empty_lines)


def main(arguments):
    try:
        with open(os.path.join(arguments.config_folder, arguments.config_file), "r") as configFile:
            config = yaml.load(configFile)
    except Exception as inst:
        exit("Failed to open or interpret config file: {}".format(inst))  # Exit if the config file can not be read
    else:
        print("Config file '{}' interpreted.".format(configFile.name))
        item_descriptions = {}
        for product in config['products']:
            if product['code'] in item_descriptions:
                print("ERROR: Multiple products with code '{}' detected in config file '{}'."
                      .format(product['code'], os.path.join(arguments.config_folder, arguments.config_file)))
                exit('DUPLICATE PRODUCT CODE')
            print("Defining product '{}'.".format(product['name']))
            item_descriptions[product['code']] = ItemDescription(code=product['code'],
                                                                 name=product['name'],
                                                                 unit_price=D(product['price']),
                                                                 print_order=product['printOrder'])
        cash_register = CashRegister(cash=config['initial']['cash'],
                                     currency_code=config['currencyCode'],
                                     storage_location=os.path.join(arguments.config_folder,
                                                                   config['cash_register_file']))
        try:
            cash_register = pickle.load(open(config['cash_register_file'], "rb"))
        except IOError as e:
            print("The cash register file '{}' does not yet exist. No data to import."
                  .format(config['cash_register_file']))
            # print("I/O error ({0}): {1}".format(e.errno, e.strerror))
        else:
            print("Data imported from the cash register file '{}'".format(config['cash_register_file']))

        sold_item_quantities = {}
        sold_item_revenues = {}
        stock_register = StockRegister(sold_item_quantities=sold_item_quantities,
                                       sold_item_revenues=sold_item_revenues,
                                       currency_code=config['currencyCode'],
                                       storage_location=os.path.join(arguments.config_folder,
                                                                     config['stock_register_file']))
        try:
            stock_register = pickle.load(open(config['stock_register_file'], "rb"))
        except IOError as e:
            print("The stock register file '{}' does not yet exist. No data to import."
                  .format(config['stock_register_file']))
            # print("I/O error ({0}): {1}".format(e.errno, e.strerror))
        else:
            print("Data imported from the stock register file '{}'".format(config['stock_register_file']))
        shopping_basket = ShoppingBasket()

        regex = re.compile(r'^\s*(?P<item_operation>[-+=]{0,1})(?P<item_quantity>\d{0,})(?P<item_code>[a-z]+)\s*$')
        # More info on regex: https://docs.python.org/2/library/re.html

        while True:
            # clear_the_screen()
            cash_register.show_one_line()
            stock_register.show_one_line(item_descriptions)
            requested_items_string = input("\n--> ")
            requested_items_list = requested_items_string.lower().split(" ")
            if requested_items_list == ['qq']:
                print("QUIT")
                break
            if requested_items_list == ['rr']:
                print("RESET")
                shopping_basket.__init__(config['currencyCode'])
            elif requested_items_list == ['nn']:
                print("Next customer!")
                cash_register, stock_register = shopping_basket.close_transaction(cash_register, stock_register)
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
                        if product_code in item_descriptions:
                            if product_operation == "+":
                                shopping_basket.add_item(item_descriptions[product_code], int(product_quantity))
                            elif product_operation == "-":
                                shopping_basket.remove_item(item_descriptions[product_code], int(product_quantity))
                            elif product_operation == "=":
                                shopping_basket.set_item(item_descriptions[product_code], int(product_quantity))
                        elif product_code == "cash" and product_operation == "+":
                            shopping_basket.add_cash(int(product_quantity))
                        elif product_code == "cash" and product_operation == "-":
                            shopping_basket.remove_cash(int(product_quantity))
                        elif product_code == "cash" and product_operation == "=":
                            shopping_basket.set_cash(int(product_quantity))
                        else:
                            print("Product with code {} is not known.".format(product_code))



        # print(itemDescriptions['iv'])
        shopping_basket = ShoppingBasket(config['currencyCode'])
        shopping_basket.add_item(item_descriptions['ik'], 4)
        shopping_basket.add_item(item_descriptions['iv'], 3)
        shopping_basket.add_item(item_descriptions['dk'], 2)
        shopping_basket.add_item(item_descriptions['db'], 1)
        shopping_basket.add_cash(30)

        # shoppingBasket.removeItem(itemDescriptions['ik'], 1)
        shopping_basket.show()
        cash_register, stock_register = shopping_basket.close_transaction(
            cash_register=cash_register,
            stock_register=stock_register)
        cash_register.show()
        stock_register.show()

    # shoppingCart.removeCash("Aha")
    # shoppingCart.setCash("Aha")
    # shoppingCart.show()
    # shoppingCart.removeItem(itemDescriptions['db'], 2)


parser = argparse.ArgumentParser(description='MyOwnPointOfSales: keeping track of cash and goods.')
parser.add_argument('--config-folder', default=".", help='Config folder, in which the config file is located')
parser.add_argument('--config-file', default="a.yaml", help='Name of config file')
args = parser.parse_args()

if __name__ == "__main__":
    main(args)
