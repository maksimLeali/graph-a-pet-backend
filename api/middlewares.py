def auth_middleware(f):
    def function_wrapper(x, m):
        print('*§*§*§*§*§*§*§*§')
        print(m.context.headers['Authorization'])
        if(m.context.headers['Authorization'] != 'Bearer 123'):
            return { "error" : 'Not authorized'}
        return f(x, m)
    return function_wrapper