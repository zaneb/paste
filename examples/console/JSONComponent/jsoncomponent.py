from Component import Component, ServletComponent
from json import jsonToObj, objToJson
from paste import httpexceptions
from cStringIO import StringIO
import traceback
from paste import wsgilib

class JSONServletComponent(ServletComponent):

    _servletMethods = ['jsonaction', 'jsonjs']

    def __init__(self, jsolaitURL='jsolait',
                 libURL='',
                 baseConfig=None,
                 jsonMethods=()):
        self.baseConfig = baseConfig
        self.jsolaitURL = jsolaitURL
        self.libURL = libURL
        self._declaredJsonMethods = list(jsonMethods)

    def actions(self):
        return ['jsonaction']

    def jsonMethods(self):
        all_methods = self._declaredJsonMethods[:]
        all_methods.extend(self.optionalMethod('jsonMethods', []))
        return all_methods

    def jsonaction(self):
        request_body = self.servlet().request().rawInput().read()
        req_data = jsonToObj(request_body)
        req_id = req_data['id']
        try:
            method_name = req_data['method']
            if method_name not in self.jsonMethods():
                raise HTTPForbidden(
                    "The method %s is not public" % method_name)
            method = getattr(self.servlet(), method_name)
            result = method(*req_data['params'])
            json_res = {'id': req_id, 'result': result, 'error': None}
            json_res = objToJson(json_res)
        except Exception, e:
            if isinstance(e, httpexceptions.HTTPException):
                raise
            out = StringIO()
            # @@: I should also report this error
            traceback.print_exc(file=out)
            json_res = {'id': req_id, 'result': None,
                        'error': out.getvalue()}
            json_res = objToJson(json_res)
        self.servlet().response().write(json_res)
        self.servlet().setView(None)

    def jsonjs(self):
        env = self.servlet().request().environ()
        jsolaitURL = self.jsolaitURL
        lib = self.libURL
        here = wsgilib.construct_url(env, False)
        here += '?_action_=jsonaction';
        if self.baseConfig:
            app_base = env['%s.base_url' % self.baseConfig]
            if not jsolaitURL.startswith('/'):
                jsolaitURL = app_base + '/' + jsolaitURL
            if not lib.startswith('/'):
                lib = app_base + '/' + lib
        text = (r'''
        <script type="text/javascript" src="%(jsolaitURL)s/init.js"></script>
        <script type="text/javascript">
        //var jsolait = importModule("jsolait");
        //jsolait.baseURL = "%(lib)s";
        //jsolait.libURL = "%(jsolaitURL)s";
        </script>
        <script type="text/javascript" src="%(jsolaitURL)s/lib/urllib.js"></script>
        <script type="text/javascript" src="%(jsolaitURL)s/lib/jsonrpc.js"></script>
        <script type="text/javascript" src="%(jsolaitURL)s/lib/lang.js"></script>
        <script type="text/javascript">
        jsonrpc = importModule("jsonrpc");
        var servlet = new jsonrpc.ServiceProxy(%(here)r, %(methods)r);
        </script>
        '''
            % {'jsolaitURL': jsolaitURL,
               'lib': lib,
               'here': here,
               'methods': self.jsonMethods()})
        return text

class JSONComponent(Component):
    _componentClass = JSONServletComponent

"""
        <script type="text/javascript" src="%(jsolaitURL)s/lib/jsolait.js"></script>
        <script type="text/javascript">
        //jsolait = importModule("jsolait");
        //jsolait.baseURL = %jsolaitURLr;
        //jsolait.libURL = %(lib)r;
        </script>
"""