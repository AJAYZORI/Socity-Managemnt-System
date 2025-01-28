from flask import Flask, jsonify, logging, request, redirect, url_for, render_template
import json
import os

app = Flask(__name__)
# File to store the data
DATA_FILE = 'society_data.json'

def save_data(data):
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(script_dir, DATA_FILE)
    
    with open(data_file_path, 'w') as file:
        json.dump(data, file, indent=4)

def load_data():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file_path = os.path.join(script_dir, DATA_FILE)
    
    if not os.path.exists(data_file_path):
        # Initialize with default data if the file doesn't exist
        default_data = {"owners": [], "expenses": [], "funds": 0}
        save_data(default_data)
        return default_data
    try:
        with open(data_file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        # Handle empty or invalid JSON file
        logging.error("Invalid JSON data. Initializing with default data.")
        default_data = {"owners": [], "expenses": [], "funds": 0}
        save_data(default_data)
        return default_data

# Add Owner
@app.route('/add_owner', methods=['GET', 'POST'])
def add_owner():
    if request.method == 'POST':
        data = load_data()
        owner = {
            "id": len(data['owners']) + 1,
            "name": request.form.get('name'),
            "flat_number": request.form.get('flat_number'),
            "phone": request.form.get('phone'),
            "maintenance": []  # Initialize maintenance as an empty list
        }
        data['owners'].append(owner)
        save_data(data)
        return redirect(url_for('index'))
    return render_template('add_owner.html')

# Add Maintenance for a Specific Owner
@app.route('/add_maintenance/<int:owner_id>', methods=['GET', 'POST'])
def add_maintenance(owner_id):
    data = load_data()
    owner = next((o for o in data['owners'] if o['id'] == owner_id), None)
    if not owner:
        return "Owner not found", 404

    if request.method == 'POST':
        maintenance = {
            "id": len(owner['maintenance']) + 1,
            "amount": float(request.form.get('amount')),
            "date": request.form.get('date')
        }
        owner['maintenance'].append(maintenance)
        data['funds'] += maintenance['amount']  # Add to total funds
        save_data(data)
        return redirect(url_for('index'))

    return render_template('add_maintenance.html', owner=owner)

# Edit Maintenance Record
@app.route('/edit_maintenance/<int:owner_id>/<int:record_id>', methods=['GET', 'POST'])
def edit_maintenance(owner_id, record_id):
    data = load_data()
    owner = next((o for o in data['owners'] if o['id'] == owner_id), None)
    if not owner:
        return "Owner not found", 404

    record = next((m for m in owner['maintenance'] if m['id'] == record_id), None)
    if not record:
        return "Maintenance record not found", 404

    if request.method == 'POST':
        record['amount'] = float(request.form.get('amount'))
        record['date'] = request.form.get('date')
        save_data(data)
        return redirect(url_for('index'))

    return render_template('edit_maintenance.html', owner=owner, record=record)

# Delete Maintenance Record
@app.route('/delete_maintenance/<int:owner_id>/<int:record_id>', methods=['POST'])
def delete_maintenance(owner_id, record_id):
    data = load_data()
    owner = next((o for o in data['owners'] if o['id'] == owner_id), None)
    if not owner:
        return "Owner not found", 404

    record = next((m for m in owner['maintenance'] if m['id'] == record_id), None)
    if record:
        data['funds'] -= record['amount']  # Subtract from total funds
        owner['maintenance'] = [m for m in owner['maintenance'] if m['id'] != record_id]
        save_data(data)
    return redirect(url_for('index'))

# Add Expense
@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    data = load_data()
    if request.method == 'POST':
        expense = {
            "id": len(data['expenses']) + 1,
            "description": request.form.get('description'),
            "amount": float(request.form.get('amount')),
            "date": request.form.get('date')
        }
        data['expenses'].append(expense)
        data['funds'] -= expense['amount']  # Deduct from total funds
        save_data(data)
        return redirect(url_for('list_expenses'))
    return render_template('add_expense.html')

# List Owners
@app.route('/owners')
def list_owners():
    data = load_data()
    return render_template('owners.html', owners=data['owners'])

# List Expenses
@app.route('/expenses')
def list_expenses():
    data = load_data()
    return render_template('expenses.html', expenses=data['expenses'])

# Edit Owner
@app.route('/edit_owner/<int:owner_id>', methods=['GET', 'POST'])
def edit_owner(owner_id):
    data = load_data()
    owner = next((o for o in data['owners'] if o['id'] == owner_id), None)
    if not owner:
        return "Owner not found", 404

    if request.method == 'POST':
        owner['name'] = request.form.get('name')
        owner['flat_number'] = request.form.get('flat_number')
        owner['phone'] = request.form.get('phone')
        save_data(data)
        return redirect(url_for('list_owners'))

    return render_template('edit_owner.html', owner=owner)

# Delete Owner
@app.route('/delete_owner/<int:owner_id>')
def delete_owner(owner_id):
    data = load_data()
    data['owners'] = [o for o in data['owners'] if o['id'] != owner_id]
    save_data(data)
    return redirect(url_for('list_owners'))

# Delete Expense
@app.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    data = load_data()
    expense = next((e for e in data['expenses'] if e['id'] == expense_id), None)
    if expense:
        data['funds'] += expense['amount']  # Add back the expense amount to funds
        data['expenses'] = [e for e in data['expenses'] if e['id'] != expense_id]
        save_data(data)
    return redirect(url_for('list_expenses'))

# Get Summary
@app.route('/summary')
def get_summary():
    data = load_data()
    
    # Calculate total maintenance collected
    total_maintenance = sum(sum(m['amount'] for m in owner['maintenance']) for owner in data['owners'])
    
    # Calculate total expenses
    total_expenses = sum(expense['amount'] for expense in data['expenses'])
    
    # Calculate net funds (Total Maintenance - Total Expenses)
    net_funds = total_maintenance - total_expenses
    
    return render_template('summary.html', data=data, total_maintenance=total_maintenance, total_expenses=total_expenses, net_funds=net_funds)

# Home Page
@app.route('/')
def index():
    data = load_data()
    
    # Calculate total maintenance collected
    total_maintenance = sum(sum(m['amount'] for m in owner['maintenance']) for owner in data['owners'])
    
    # Calculate total expenses
    total_expenses = sum(expense['amount'] for expense in data['expenses'])
    
    # Calculate net funds (Total Maintenance - Total Expenses)
    net_funds = total_maintenance - total_expenses
    
    return render_template('index.html', data=data, total_maintenance=total_maintenance, total_expenses=total_expenses, net_funds=net_funds)

if __name__ == '__main__':
    app.run(debug=True)