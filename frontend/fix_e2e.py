with open("c:\\Users\\Admin\\Desktop\\TEST_1002\\test\\frontend\\e2e\\todos.spec.ts", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("getByRole('link', { name: 'Register' })", "getByRole('link', { name: 'Sign up' })")
content = content.replace("getByRole('heading', { name: 'Login' })", "getByRole('heading', { name: 'Welcome Back' })")
content = content.replace("getByRole('button', { name: 'Register' })", "getByRole('button', { name: 'Create Account' })")
content = content.replace("getByRole('button', { name: 'Login' })", "getByRole('button', { name: 'Sign In' })")
content = content.replace("getByLabel('Password')", "getByLabel('Password', { exact: true })")

with open("c:\\Users\\Admin\\Desktop\\TEST_1002\\test\\frontend\\e2e\\todos.spec.ts", "w", encoding="utf-8") as f:
    f.write(content)
