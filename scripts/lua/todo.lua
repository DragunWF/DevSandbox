username = nil
todo_list = {}

function main() 
    print("Program starting...\n")
    greet_user()
    simulate_todo_menu()
    print("\nProgram is now ending...")
end

function greet_user()
    username = input("Welcome! What is your username")
    print("Greetings! " .. username .. ", welcome to Dragun's practice project for the Lua scripting language.\n")
end

function simulate_todo_menu()
    local chosen_command = choose_command()

    while chosen_command ~= "exit" do
        if chosen_command == "view" then
            display_todo_list()
        elseif chosen_command == "add" then
            simulate_add_menu()
        elseif chosen_command == "remove" then
            simulate_remove_menu()
        elseif chosen_command == "update" then
            simulate_update_menu()
        end
        chosen_command = choose_command()
    end

    print("\nThank you, " .. username .. "!" .. " For trying out Dragun's practice program for Lua")
end

function choose_command()
    local command_list = {
        add = "Adds an item to the list.",
        remove = "Removes an item from the list.",
        update = "Removes an item from the list.",
        view = "Displays the list.",
        exit = "Exit the program"
    }

    print("\nCommands:")
    for key, value in pairs(command_list) do
        print("- " .. key .. " : " .. value)
    end

    local chosen_command = string.lower(input("\nSelect a command"))
    if not contains_key(command_list, chosen_command) then
        print("Please select a valid command!")
        return choose_command()
    end

    return chosen_command
end

function display_todo_list()
    local wall = "========================"
    print("\n" .. wall .. "\nTodo List: " .. "[" .. #todo_list .. " item(s)]")

    if #todo_list > 0 then
        for i = 1, #todo_list do
            print(i .. ". " .. todo_list[i])
        end
    else
        print("<empty>")
    end

    print(wall .. "\n")
end

function simulate_add_menu()
    add_item()
    display_todo_list()

    while bool_input("Do you want to add more items to your list?") do
        add_item()
        display_todo_list()
    end
end

function add_item()
    local item = input("Enter an item name")
    todo_list[#todo_list + 1] = item
    print("\"" .. item .. "\"" .. " has been added to the list!")
end

function simulate_remove_menu()
    if #todo_list <= 0 then
        print("There are no items to remove in the list!")
        return
    end

    display_todo_list()
    remove_item()
    display_todo_list()

    while bool_input("Do you want to remove more items from your list?") do
        if #todo_list <= 0 then
            print("There are no more items to remove in the list!")
            break
        end
        remove_item()
        display_todo_list()
    end
end

function remove_item()
    local item_id = input_item_id("Remove item by ID")
    local removed_item = todo_list[item_id]
    table.remove(todo_list, item_id)
    print("\"" .. removed_item .. "\"" .. " has been removed from the list!")
end

function simulate_update_menu()
    if #todo_list <= 0 then
        print("There are no items to update in the list!")
        return
    end

    display_todo_list()
    update_item()
    display_todo_list()

    while bool_input("Do you want to update more items from your list?") do
        update_item()
        display_todo_list()
    end
end

function update_item()
    local item_id = input_item_id("Update item by ID")
    local item_before_update = todo_list[item_id]
    
    local updated_item = input("Enter a new name for the item \"" .. item_before_update .. "\"")
    todo_list[item_id] = updated_item
    print("\"" .. item_before_update .. "\"" .. " has been updated to " .. "\"" .. updated_item .. "\"")
end

function input(prompt)
    io.write(prompt .. ": ")
    local output = io.read()

    if output == "" then
        print("Input must not be empty!")
        return input(prompt)
    end

    return output
end

function input_item_id(prompt)
    io.write(prompt .. " [Enter Number]: ")
    local id = tonumber(io.read())

    if not id then
        print("Invalid input! Please make sure to enter a number.")
        return input_item_id(prompt)
    end
    if id <= 0 or id > #todo_list then
        print("Please enter a number within the range of [" .. 1 .. "-" .. #todo_list .. "]")
        return input_item_id(prompt)
    end

    return id
end

function bool_input(prompt)
    local valid_choices = {"y", "yes", "no", "n"}

    io.write(prompt .. " (yes/no): ")
    local choice = string.lower(io.read())
    if contains_value(valid_choices, choice) then
        return choice == "y" or choice == "yes"
    end
    
    print("Invalid choice! Type either \"yes\" or \"no\"")
    return bool_input(prompt)
end

function contains_value(table, target)
    return contains(table, target, false)
end

function contains_key(table, target)
    return contains(table, target, true)
end

function contains(table, target, find_key_flag)
    for key, value in pairs(table) do
        if (find_key_flag and key == target) or (not find_key_flag and value == target) then
            return true
        end
    end
    return false
end

main()