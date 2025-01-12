username = nil
todo_list = {}

function main() 
    print("Program starting...\n")
    greet_user()
    simulate_todo_menu()
    print("\nProgram is now ending...")
end

function greet_user()
    io.write("Welcome! What is your username: ")
    username = io.read()
    if username == "" then
        print("Please enter a username!")
        greet_user()
        return
    end
    print("Greetings! " .. username .. ", welcome to Dragun's practice project for the Lua scripting language.\n")
end

function simulate_todo_menu()
    display_todo_list()

    while bool_input("Do you want to add an item to your list? ") do
        add_item()
        display_todo_list()
    end

    while bool_input("Do you want to remove an item from your list? ") do
        remove_item()
        display_todo_list()
        if #todo_list <= 0 then
            print("There are no more items in the list!")
            break
        end
    end

    print("\nThank you, " .. username .. "!" .. " For trying out Dragun's practice program for Lua")
end

function display_todo_list()
    print("\nTodo List: " .. "[" .. #todo_list .. " item(s)]")
    if #todo_list > 0 then
        for i = 1, #todo_list do
            print(i .. ". " .. todo_list[i])
        end
    else
        print("<empty>")
    end
    print()
end

function bool_input(prompt)
    local valid_choices = {"y", "yes", "no", "n"}

    io.write(prompt .. "(yes/no): ")
    local choice = string.lower(io.read())
    if contains(valid_choices, choice) then
        return choice == "y" or choice == "yes"
    end
    
    print("Invalid choice! Type either \"yes\" or \"no\"")
    return bool_input(prompt)
end

function contains(table, target)
    for _, value in pairs(table) do
        if value == target then
            return true
        end
    end
    return false
end

function add_item()
    io.write("Enter item: ")
    local item = io.read()
    if item == "" then
        print("Enter an item name!")
        add_item()
        return
    end

    todo_list[#todo_list + 1] = item
    print("\"" .. item .. "\"" .. " has been added to the list!")
end

function remove_item()
    io.write("Remove item by ID [Enter Number]: ")
    local item_id = tonumber(io.read())

    if not item_id then
        print("Invalid input! Please make sure to enter a number.")
        remove_item()
    elseif item_id <= 0 or item_id > #todo_list then
        print("Please enter a number within the range of [" .. 1 .. "-" .. #todo_list .. "]")
        remove_item()
    else
        local itemNameToBeRemoved = todo_list[item_id]
        table.remove(todo_list, item_id)
        print("\"" .. itemNameToBeRemoved .. "\"" .. " has been removed from the list!")
    end
end

main()