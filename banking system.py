def display_menu():
	"""Display the main menu options."""
	print("\n========== Banking System ==========")
	print("1. Create Account")
	print("2. Login")
	print("3. Check Balance")
	print("4. Deposit Money")
	print("5. Withdraw Money")
	print("6. Transfer Money")
	print("7. View Transaction History")
	print("8. Change PIN")
	print("9. Logout")
	print("10. Exit")
	print("====================================")


print("Welcome to Banking System")

while True:
	display_menu()
	choice = input("Enter your choice: ")

	if choice == "10":
		print("Thank you for using Banking System.")
		break
	else:
		print("This feature will be added in the next steps.")
