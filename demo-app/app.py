from flask import Flask, render_template, request

app = Flask(__name__)


# -------------------------
# TENANT A DATA
# -------------------------

members = {
    "12345": {
        "name": "Alice Johnson",
        "checking": "$1,280.40",
        "savings": "$4,320.50"
    },

    "67890": {
        "name": "Robert Smith",
        "checking": "$850.25",
        "savings": "$2,110.75"
    },

    "55555": {
        "name": "Maria Garcia",
        "checking": "$3,400.00",
        "savings": "$7,890.10"
    }
}


# -------------------------
# TENANT B DATA
# -------------------------

customers = {
    "C1001": {
        "name": "John Miller",
        "current": "$2,450.25",
        "savings": "$8,120.75"
    },

    "C1002": {
        "name": "Sarah Wilson",
        "current": "$1,720.40",
        "savings": "$5,600.20"
    }
}


# -------------------------
# TENANT A
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/member/search", methods=["POST"])
def search_member():

    member_id = request.form.get("member_id")

    member = members.get(member_id)

    if not member:
        return render_template(
            "index.html",
            error="Member not found"
        )

    return render_template(
        "member.html",
        member_id=member_id,
        member=member
    )


# -------------------------
# TENANT B
# -------------------------

@app.route("/tenant-b")
def tenant_b_home():

    return render_template(
        "tenant_b.html"
    )


@app.route(
    "/tenant-b/customer/search",
    methods=["POST"]
)
def search_customer():

    customer_id = request.form.get(
        "customer_id"
    )

    customer = customers.get(
        customer_id
    )

    if not customer:
        return render_template(
            "tenant_b.html",
            error="Customer not found"
        )

    return render_template(
        "tenant_b_customer.html",
        customer_id=customer_id,
        customer=customer
    )


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )