#!/usr/bin/python3

def read_text_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def create_html_with_text(file_path, html_template_path, output_html_path):
    text_content = read_text_file(file_path)
    with open(html_template_path, 'r') as file:
        html_content = file.read()

    html_content = html_content.replace('<!-- Text content will go here -->', text_content)

    with open(output_html_path, 'w') as file:
        file.write(html_content)

# Example usage
create_html_with_text('temp/0.txt', 'web/template_html.html', '/var/www/html/output/0.html')
create_html_with_text('temp/1.txt', 'web/template_html.html', '/var/www/html/output/1.html')
create_html_with_text('temp/2.txt', 'web/template_html.html', '/var/www/html/output/2.html')
create_html_with_text('temp/3.txt', 'web/template_html.html', '/var/www/html/output/3.html')
create_html_with_text('temp/4.txt', 'web/template_html.html', '/var/www/html/output/4.html')
create_html_with_text('temp/5.txt', 'web/template_html.html', '/var/www/html/output/5.html')
create_html_with_text('temp/6.txt', 'web/template_html.html', '/var/www/html/output/6.html')
create_html_with_text('temp/7.txt', 'web/template_html.html', '/var/www/html/output/7.html')
create_html_with_text('temp/8.txt', 'web/template_html.html', '/var/www/html/output/8.html')
create_html_with_text('temp/9.txt', 'web/template_html.html', '/var/www/html/output/9.html')
create_html_with_text('temp/10.txt', 'web/template_html.html', '/var/www/html/output/10.html')
create_html_with_text('temp/11.txt', 'web/template_html.html', '/var/www/html/output/11.html')
create_html_with_text('temp/12.txt', 'web/template_html.html', '/var/www/html/output/12.html')
create_html_with_text('temp/13.txt', 'web/template_html.html', '/var/www/html/output/13.html')
create_html_with_text('temp/14.txt', 'web/template_html.html', '/var/www/html/output/14.html')

