import commune as c
from typing import *

class Namespace(c.Module):
    network : str = 'local'

    @classmethod
    def register_server(cls, name:str, address:str, network=network) -> None:
        namespace = cls.get_namespace(network)
        namespace[name] = address
        cls.put_namespace(network, namespace)
        return {'status': 'success', 'msg': f'Block {name} registered to {network}.'}

    @classmethod
    def deregister_server(cls, name:str, network=network) -> Dict:

        namespace = cls.get_namespace(network)
        if name in namespace:
            del namespace[name]
            cls.put_namespace(network, namespace)
            return {'status': 'success', 'msg': f'Block {name} deregistered.'}
        else:
            return {'status': 'failure', 'msg': f'Block {name} not found.'}

    @classmethod


    def get_module(cls, name:str, network:str=network) -> dict:
        namespace = cls.get_namespace(network)
        return namespace.get(name, None)

    @classmethod
    def get_namespace(cls, network:str = 'local', update:bool = True, search:str = None ) -> dict:
        if network == None: 
            network = cls.network

        if network == 'subspace':
            namespace =  c.module(network).namespace()
        else:
            namespace = cls.get(network, {})
        if search != None:
            namespace = {k:v for k,v in namespace.items()}
        return namespace
    @classmethod
    def put_namespace(cls, network:str, namespace:dict) -> None:
        assert isinstance(namespace, dict), 'Namespace must be a dict.'
        cls.put(network, namespace)
        return {'status': 'success', 'msg': f'Namespace {network} updated.'}

    @classmethod
    def rm_namespace(cls,network:str) -> None:
        if cls.exists(network):
            cls.rm(network)
            return {'status': 'success', 'msg': f'Namespace {network} removed.'}
        else:
            return {'status': 'failure', 'msg': f'Namespace {network} not found.'}
    @classmethod
    def name2address(cls, name:str, network:str=network ):
        namespace = cls.get_namespace(network=network)
        address =  namespace.get(name, None)
        ip = c.ip()
    
        address = address.replace(c.default_ip, ip)
        assert ip in address, f'ip {ip} not in address {address}'
        return address
    @classmethod
    def networks(cls) -> dict:
        return [p.split('/')[-1].split('.')[0] for p in cls.ls()]
    
    @classmethod
    def namespace_exists(cls, network:str) -> bool:
        return cls.exists(network)

    @classmethod
    def test(cls):
        network = 'test'
        network2  = 'test2'
        cls.rm_namespace(network)
        cls.rm_namespace(network2)

        assert cls.get_namespace(network) == {}, 'Namespace not empty.'
        cls.register_server('test', 'test', network=network)
        assert cls.get_namespace(network) == {'test': 'test'}, f'Namespace not updated. {cls.get_namespace(network)}'

        assert cls.get_namespace(network2) == {}
        cls.register_server('test', 'test', network=network2)
        assert cls.get_namespace(network) == {'test': 'test'}, f'Namespace not restored. {cls.get_namespace(network)}'
        cls.deregister_server('test', network=network2)
        assert cls.get_namespace(network2) == {}
        cls.rm_namespace(network)
        assert cls.namespace_exists(network) == False
        cls.rm_namespace(network2)
        assert cls.namespace_exists(network2) == False
        
        return {'status': 'success', 'msg': 'Namespace tests passed.'}
    
    @classmethod
    def modules(cls, network:List=network) -> List[str]:
        return list(cls.get_namespace(network=network).keys())
    
    @classmethod
    def addresses(cls, network:str=network) -> List[str]:
        return list(cls.get_namespace(network=network).values())
    
    @classmethod
    def module_exists(cls, module:str, network:str=network) -> bool:
        namespace = cls.get_namespace(network=network)
        return bool(module in namespace)

    @classmethod
    def update_namespace(cls,
                        chunk_size:int=10, 
                        timeout:int = 10,
                        full_scan:bool = False,
                        network:str = network,)-> dict:
        '''
        The module port is where modules can connect with each othe.
        When a module is served "module.serve())"
        it will register itself with the namespace_local dictionary.
        '''

        namespace = cls.get_namespace(network=network, update=False) # get local namespace from redis
        addresses = c.copy(list(namespace.values()))

        if full_scan == True or len(addresses) == 0:
            addresses = [c.default_ip+':'+str(p) for p in c.used_ports()]

        c.print(f'Updating local namespace with {len(addresses)} addresses', color='green')

        for i in range(0, len(addresses), chunk_size):
            addresses_chunk = addresses[i:i+chunk_size]
            names_chunk = c.gather([c.async_call(address, fn='server_name', timeout=timeout) for address in addresses_chunk])
            for i in range(len(names_chunk)):
                if isinstance(names_chunk[i], str):
                    namespace[names_chunk[i]] = addresses_chunk[i]
            
        for k, v in namespace.items():
            namespace[k] = c.default_ip + ':' + v.split(':')[-1]

        return namespace
    
    @classmethod
    def migrate_namespace(cls, network:str='local'):
        namespace = c.get_json('local_namespace', {})
        c.put_namespace(network, namespace)
