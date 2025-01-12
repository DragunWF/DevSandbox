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
    display_todo_list()
    local command_list = {
        "add : Adds an item to the list.",
        "remove : Removes an item from the list.",
        "update : Removes an item from the list.",
        "view : View the list."
    }

    print("Commands:")
    for i = 1, #command_list do
        print("- " .. command_list[i])
    end

    print("\nThank you, " .. username .. "!" .. " For trying out Dragun's practice program for Lua")
end

function simulate_add_menu()
    add_item()
    while bool_input("Do you want to add more items to your list?") do
        add_item()
        display_todo_list()
    end
end

function simulate_remove_menu()
    if #todo_list <= 0 then
        print("There are no items to remove in the list!")
        return
    end

    remove_item()
    while bool_input("Do you want to remove more items from your list?") do
        remove_item()
        display_todo_list()
        if #todo_list <= 0 then
            print("There are no more items to remove in the list!")
            break
        end
    end
end

function simulate_update_menu()

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

    io.write(prompt .. " (yes/no): ")
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
    local item = input("Enter an item name")
    todo_list[#todo_list + 1] = item
    print("\"" .. item .. "\"" .. " has been added to the list!")
end

function remove_item()
    local item_id = input_id("Remove item by ID")
    local removed_item = todo_list[item_id]
    table.remove(todo_list, item_id)
    print("\"" .. removed_item .. "\"" .. " has been removed from the list!")
end

function update_item()
    local item_id = input_id("Update item by ID")
    local item_before_update = todo_list[item_id]
    
    local updated_item = input("Enter a new name for the item \"" .. item_before_update "\"")
    todo_list[item_id] = updated_item
    print("\"" .. item_before_update .. "\"" .. " has been updated to " .. "\"" .. updated_item .. "\"")
end

function input_id(prompt)
    io.write(prompt .. "[Enter Number]: ")
    local id = tonumber(io.read())

    if not id then
        print("Invalid input! Please make sure to enter a number.")
        return input_id(prompt)
    end
    if id <= 0 or id > #todo_list then
        print("Please enter a number within the range of [" .. 1 .. "-" .. #todo_list .. "]")
        return input_id(prompt)
    end

    return id
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

main()