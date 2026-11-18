"""Generates tech_bank_policies.pdf (sample policies, FAQs and chatbot rules for the fictional Tech Bank)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

SECTIONS = [
    ("About Tech Bank", [
        "Tech Bank: Tech Bank is a digital-first bank in Pakistan that offers savings accounts, current accounts, debit and credit cards, personal loans, home financing, car financing and mobile banking.",
        "Head Office: Tech Bank's head office is located in Karachi, Pakistan. The bank has branches in all major cities including Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Multan and Peshawar.",
        "Branch Timings: Branches are open Monday to Friday from 9:00 am to 5:00 pm and on Saturday from 9:00 am to 1:00 pm. Branches are closed on Sunday and on public holidays.",
        "Helpline: The 24/7 Tech Bank helpline number is 111-832-265. Customers can also email support@techbank.example. Complaints and general questions are answered within 2 working days.",
    ]),
    ("Account Opening", [
        "Documents Required: To open an account a customer needs a valid CNIC (or smart card), one recent passport-size photograph, a mobile number registered in the customer's own name, and proof of income for current accounts.",
        "Minimum Age: A customer must be at least 18 years old to open an account. Minors can have a Junior Savings Account that is operated by a parent or legal guardian.",
        "Savings Account: The minimum opening deposit for a Tech Bank Savings Account is 5,000 rupees. The account earns profit at up to 12 percent per year, paid monthly, based on the average daily balance.",
        "Current Account: The minimum opening deposit for a Current Account is 25,000 rupees. A Current Account does not earn profit and is designed for business and frequent transactions.",
        "Digital Account: Customers can open a Digital Account from the Tech Bank mobile app in about 10 minutes by uploading their CNIC and taking a selfie. The minimum opening deposit is 1,000 rupees.",
        "Account Activation: A new account is activated within 24 hours after all documents are verified. The customer is informed by SMS when the account is ready.",
    ]),
    ("Fees and Charges", [
        "Monthly Maintenance Fee: A Savings Account has no monthly fee if the average balance stays above 10,000 rupees. If the balance is lower, a fee of 300 rupees per month is charged. A Current Account has a monthly fee of 500 rupees.",
        "Debit Card Fee: The annual debit card fee is 1,500 rupees. The first year is free for new customers. A replacement for a lost or damaged card costs 1,000 rupees.",
        "ATM Withdrawal: Withdrawing cash from a Tech Bank ATM is free. Withdrawing from another bank's ATM costs 35 rupees per transaction. The daily ATM withdrawal limit is 100,000 rupees.",
        "Fund Transfer Fees: Transfers to another Tech Bank account are free. Transfers to other banks using Raast are free up to 50,000 rupees per day. Transfers through IBFT to other banks cost 25 rupees per transaction.",
        "Cheque Book: The first cheque book of 25 leaves is free every year. Additional cheque books cost 500 rupees. A cheque returned for insufficient balance carries a penalty of 1,000 rupees.",
        "Account Statement: Statements can be downloaded free from the mobile app and internet banking. A printed statement from a branch costs 200 rupees per request.",
    ]),
    ("Cards", [
        "Debit Card Limits: The daily limit for POS and online shopping on a debit card is 200,000 rupees. Customers can change their limits from the mobile app.",
        "Credit Card Eligibility: To apply for a Tech Bank Credit Card a customer must be between 21 and 60 years old and have a minimum monthly income of 50,000 rupees. Salaried and self-employed people can apply.",
        "Credit Card Charges: The credit card markup rate is 3 percent per month on the unpaid balance. The minimum payment due is 5 percent of the total outstanding amount. A late payment fee of 1,500 rupees is charged if the minimum payment is missed.",
        "Lost or Stolen Card: If a card is lost or stolen the customer must block it immediately from the mobile app or by calling the 24/7 helpline 111-832-265. A blocked card cannot be used again. A new card is delivered within 5 working days.",
        "Card Delivery: A new debit card is delivered to the customer's address within 7 working days, or the customer can collect it from the branch.",
        "Card PIN: A customer who forgets the card PIN can reset it from the mobile app or at any Tech Bank ATM. Tech Bank staff will never ask for a PIN.",
    ]),
    ("Loans and Financing", [
        "Personal Loan: Tech Bank offers personal loans from 100,000 to 3,000,000 rupees with a repayment period of 12 to 60 months. The markup rate starts at 18 percent per year. A processing fee of 1 percent of the loan amount applies.",
        "Personal Loan Eligibility: The applicant must be 22 to 60 years old, have a minimum monthly income of 40,000 rupees and have at least 6 months of work history. Salary slips and 6 months of bank statements are required.",
        "Home Financing: Home financing is available up to 25,000,000 rupees for up to 20 years. The customer must pay a down payment of at least 20 percent of the property price.",
        "Car Financing: Car financing is available for new and used cars with a repayment period of up to 7 years. The customer must pay a down payment of at least 15 percent of the car price and arrange comprehensive insurance.",
        "Loan Approval Time: A loan application is usually decided within 5 to 7 working days after all documents are submitted. Funds are transferred to the customer's account after approval.",
        "Early Repayment: A customer can repay a loan early. An early settlement fee of 2 percent of the remaining principal amount is charged.",
        "Late Installment: If a loan installment is not paid on time, a late payment charge of 1,000 rupees is added and the delay is reported to the credit bureau.",
    ]),
    ("Digital Banking", [
        "Mobile App: The Tech Bank mobile app is available for Android and iPhone. Customers can check balance, send money, pay bills, top up mobile credit, block cards and apply for products from the app.",
        "Registration: To register for mobile banking, download the app, enter your CNIC and registered mobile number, and enter the one-time password (OTP) sent by SMS. Then create a password and set up fingerprint or face login.",
        "Forgot Password: A customer who forgot the app password can tap 'Forgot Password', verify with an OTP sent to the registered mobile number and set a new password. If the mobile number has changed, the customer must visit a branch.",
        "Bill Payment: Utility bills (electricity, gas, water, internet) and mobile credit can be paid from the app at no extra charge. Payments are posted instantly.",
        "Raast and Transfer Limits: The daily transfer limit from the app is 500,000 rupees. A customer can request a higher limit by visiting a branch with supporting documents.",
        "Failed Transaction: If money is deducted but the transaction fails, the amount is automatically returned to the customer's account within 3 to 5 working days. If it is not returned, the customer should contact the helpline.",
    ]),
    ("Security", [
        "Never Share Details: Tech Bank staff will never ask for your PIN, password, OTP or full card number by phone, SMS, WhatsApp or email. Never share these with anyone, even if they claim to be from Tech Bank.",
        "Fraud Reporting: If a customer notices an unauthorized transaction, they must report it to the helpline 111-832-265 within 24 hours. The bank will investigate and, if the fraud is confirmed, the amount will be refunded within 10 working days.",
        "Suspicious Messages: Customers should ignore links in suspicious messages. Tech Bank will only send official links from its verified website and app.",
        "Account Freeze: Tech Bank may temporarily freeze an account if suspicious activity is detected. The customer is informed by SMS and must visit a branch with CNIC to reactivate the account.",
    ]),
    ("Remittances and Foreign Currency", [
        "Home Remittance: Money sent to Pakistan from abroad can be received in a Tech Bank account. Tech Bank charges no fee on incoming home remittances. The money is usually credited within 24 hours.",
        "Foreign Currency Account: Tech Bank offers foreign currency accounts in US dollars, British pounds and euros. The minimum opening deposit is 500 US dollars or equivalent.",
    ]),
    ("Account Closure, Dormant Accounts and Complaints", [
        "Closing an Account: A customer can close an account by submitting a written request at a branch with their CNIC and returning the unused cheque book and debit card. A closure fee of 500 rupees applies if the account is closed within 6 months of opening.",
        "Dormant Account: An account with no customer transaction for 12 months is marked dormant. To reactivate it the customer must visit a branch with CNIC.",
        "Complaint Process: Customers can file a complaint through the app, the helpline, email or a branch. Tech Bank resolves complaints within 7 working days. If the customer is not satisfied, they can approach the Banking Mohtasib of Pakistan.",
        "Change of Details: To change the mobile number, address or email, the customer must visit a branch with their CNIC. The change is updated within 2 working days.",
    ]),
    ("Chatbot Rules", [
        "Rule 1 - Language: Always reply in the same language in which the customer asks the question, for example English, Urdu, Roman Urdu or another language. If the language is not clear, reply in English.",
        "Rule 2 - Tone: Be polite, short, clear and professional. Greet the customer when they greet you. Use simple words that every customer can understand.",
        "Rule 3 - Accuracy: Answer only from the official Tech Bank policy information. Never guess or invent fees, rates, limits or timings. If the information is not available, politely say so and ask the customer to call the helpline 111-832-265 or visit a branch.",
        "Rule 4 - Security: Never ask the customer for their PIN, password, OTP, full card number or CVV. If the customer shares such details, warn them not to share them with anyone.",
        "Rule 5 - Scope: Only answer questions related to Tech Bank and general banking services. For unrelated questions such as politics, religion, medical, legal or investment advice, politely say that you can only help with Tech Bank services.",
        "Rule 6 - Personal Accounts: The chatbot cannot see account balances, transactions or personal data, and cannot perform transactions. For these, guide the customer to the mobile app, internet banking or the helpline.",
        "Rule 7 - Emergencies: For a lost or stolen card, fraud or an unauthorized transaction, always tell the customer to block the card in the app and call the 24/7 helpline 111-832-265 immediately.",
    ]),
]


def build(path="tech_bank_policies.pdf"):
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontSize=22, spaceAfter=6)
    sub = ParagraphStyle("sub", parent=styles["Normal"], alignment=1, textColor="#555555", spaceAfter=18)
    h = ParagraphStyle("h", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10.5, leading=15, spaceAfter=7)

    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm, title="Tech Bank Policies and FAQs")
    story = [Paragraph("Tech Bank", title),
             Paragraph("Customer Policies, FAQs and Chatbot Rules (sample document)", sub)]
    for heading, items in SECTIONS:
        story.append(Paragraph(heading, h))
        for item in items:
            topic, text = item.split(":", 1)
            story.append(Paragraph(f"<b>{topic}:</b>{text}", body))
    doc.build(story)
    print("Created", path)


if __name__ == "__main__":
    build()
