def get_mail_base_html_template(mail_body: str) -> str:

    return f"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="Content-Type" content="text/html charset=UTF-8" />
            <style>
                body {{
                    font-family: sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f4;
                }}
                .container {{
                    max-width: 600px;
                    margin: auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                }}
                .logo {{
                    display: block;
                    width: 150px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    font-size: 24px;
                    color: #333333;
                    margin-bottom: 20px;
                }}
                p {{
                    font-size: 16px;
                    color: #555555;
                    margin-bottom: 10px;
                }}
                a {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #121312;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <img src="cid:safe-logo-img" alt="Safe Dashboard Logo" class="logo">
                {mail_body}
            </div>
        </body>
    </html>
    """
