import json
import os
import pathlib
import pickle
import subprocess

import appdirs
import click

rsr_dir = pathlib.Path.home() / 'src' / 'github.com' / 'reserve-protocol' / 'protocol'

os.chdir(rsr_dir)

# list manually compiled from scripts/verification/*.js
all_contracts = {
    'facadeWrite': 'contracts/facade/FacadeWrite.sol:FacadeWrite',
    'main': 'contracts/p1/Main.sol:MainP1',
    'components': {
        'assetRegistry': 'contracts/p1/AssetRegistry.sol:AssetRegistryP1',
        'backingManager': 'contracts/p1/BackingManager.sol:BackingManagerP1',
        'basketHandler': 'contracts/p1/BasketHandler.sol:BasketHandlerP1',
        'broker': 'contracts/p1/Broker.sol:BrokerP1',
        'distributer': 'contracts/p1/Distributor.sol:DistributorP1',
        'furnace': 'contracts/p1/Furnace.sol:FurnaceP1',
        'rsrTrader': 'contracts/p1/RevenueTrader.sol:RevenueTraderP1',
        'rTokenTrader': 'contracts/p1/RevenueTrader.sol:RevenueTraderP1',
        'rToken': 'contracts/p1/RToken.sol:RTokenP1',
        'stRSR': 'contracts/p1/StRSRVotes.sol:StRSRP1Votes',
    },
    'rTokenAsset': 'contracts/plugins/assets/RTokenAsset.sol:RTokenAsset',
    'governance': 'contracts/plugins/governance/Governance.sol:Governance',
    'timelock': '@openzeppelin/contracts/governance/TimelockController.sol:TimelockController',

#     'assets': {
#         'stkAAVE': ??,
#         'COMP': ??,
#     }

    'collateral': {
        'DAI': 'contracts/plugins/assets/FiatCollateral.sol:FiatCollateral',
        'USDC': 'contracts/plugins/assets/FiatCollateral.sol:FiatCollateral',
        'USDT': 'contracts/plugins/assets/FiatCollateral.sol:FiatCollateral',
        'USDP': 'contracts/plugins/assets/FiatCollateral.sol:FiatCollateral',
        'TUSD': 'contracts/plugins/assets/FiatCollateral.sol:FiatCollateral',
        'BUSD': 'contracts/plugins/assets/FiatCollateral.sol:FiatCollateral',
        'aDAI': 'contracts/plugins/assets/ATokenFiatCollateral.sol:ATokenFiatCollateral',
        'aUSDC': 'contracts/plugins/assets/ATokenFiatCollateral.sol:ATokenFiatCollateral',
        'aUSDT': 'contracts/plugins/assets/ATokenFiatCollateral.sol:ATokenFiatCollateral',
        'aBUSD': 'contracts/plugins/assets/ATokenFiatCollateral.sol:ATokenFiatCollateral',
        'cDAI': 'contracts/plugins/assets/CTokenFiatCollateral.sol:CTokenFiatCollateral',
        'cUSDC': 'contracts/plugins/assets/CTokenFiatCollateral.sol:CTokenFiatCollateral',
        'cUSDT': 'contracts/plugins/assets/CTokenFiatCollateral.sol:CTokenFiatCollateral',
        'cWBTC': 'contracts/plugins/assets/CTokenNonFiatCollateral.sol:CTokenNonFiatCollateral',
        'cETH': 'contracts/plugins/assets/CTokenSelfReferentialCollateral.sol:CTokenSelfReferentialCollateral',
        'WBTC': 'contracts/plugins/assets/NonFiatCollateral.sol:NonFiatCollateral',
        'WETH': 'contracts/plugins/assets/SelfReferentialCollateral.sol:SelfReferentialCollateral',
        'EURT': 'contracts/plugins/assets/EURFiatCollateral.sol:EURFiatCollateral',
    },

#     'prerequisites': {
#         'RSR': ??,
#         'RSR_FEED': ??,
#         'GNOSIS_EASY_AUCTION': ??,
#     },

    'rewardableLib': 'contracts/p1/mixins/RewardableLib.sol:RewardableLibP1',
    'tradingLib': 'contracts/p1/mixins/TradingLib.sol:TradingLibP1',
    'rTokenPricingLib': 'contracts/plugins/assets/RTokenPricingLib.sol:RTokenPricingLib',
    'oracleLib': 'contracts/plugins/assets/OracleLib.sol:OracleLib',
    'facade': 'contracts/facade/Facade.sol:FacadeP1',
    'facadeWriteLib': 'contracts/facade/lib/FacadeWriteLib.sol:FacadeWriteLib',
    # 'facadeWrite': 'contracts/facade/FacadeWrite.sol:FacadeWrite',
    'deployer': 'contracts/p1/Deployer.sol:DeployerP1',
    'rsrAsset': 'contracts/plugins/assets/Asset.sol:Asset',
    'implementations': {
        'main': 'contracts/p1/Main.sol:MainP1',
        'trade': 'contracts/plugins/trading/GnosisTrade.sol:GnosisTrade',
        'components': {
            'assetRegistry': 'contracts/p1/AssetRegistry.sol:AssetRegistryP1',
            'backingManager': 'contracts/p1/BackingManager.sol:BackingManagerP1',
            'basketHandler': 'contracts/p1/BasketHandler.sol:BasketHandlerP1',
            'broker': 'contracts/p1/Broker.sol:BrokerP1',
            'distributer': 'contracts/p1/Distributor.sol:DistributorP1',
            'furnace': 'contracts/p1/Furnace.sol:FurnaceP1',
            'rsrTrader': 'contracts/p1/RevenueTrader.sol:RevenueTraderP1',
            'rTokenTrader': 'contracts/p1/RevenueTrader.sol:RevenueTraderP1',
            'rToken': 'contracts/p1/RToken.sol:RTokenP1',
            'stRSR': 'contracts/p1/StRSRVotes.sol:StRSRP1Votes',
        },
    },

}

def walk(d, prefix=[]):
    res = []
    for k, v in d.items():
        if type(v) is str:
            res.append((prefix + [k], v))
        else:
            res.extend(walk(v, prefix + [k]))
    return res

def flatten(xs):
    return {'.'.join(ks): v for ks, v in xs}

metas = flatten(walk(all_contracts))

cache_dir = appdirs.user_cache_dir('github_jeremyschlatter_rsr-tools')

def memo_build_info(path):
    path = pathlib.Path(path).resolve()
    os.makedirs(cache_dir, exist_ok=True)
    cached = pathlib.Path(cache_dir) / path.name
    if cached.is_file():
        with open(cached, 'rb') as f:
            return pickle.load(f)
    with open(path) as f:
        build_info = json.load(f)['output']['sources']

        clean = {}

        for c in metas.values():
            (p, name) = c.split(':')
            for node in build_info[p]['ast']['nodes']:
                if node['nodeType'] == 'ContractDefinition' and node['name'] == name:
                    fns = {}
                    for node in node['nodes']:
                        if node['nodeType'] == 'FunctionDefinition':
                            d = node.get('documentation')
                            fns[node['name']] = d
                    if not p in clean:
                        clean[p] = {}
                    clean[p][name] = fns

    with open(cached, 'wb') as f:
        pickle.dump(clean, f)

    return clean

def abi_and_ast(contract):
    (path, name) = contract.split(':')
    with open(f'artifacts/{path}/{name}.json') as f:
        abi = json.load(f)['abi']
    with open(f'artifacts/{path}/{name}.dbg.json') as f:
        build_info = memo_build_info(f'artifacts/{path}/{json.load(f)["buildInfo"]}')
    return (abi, build_info[path][name])

@click.group()
def cli():
    pass

def setup():

    chainid = 31337

    blobs = [
        f'{chainid}-{x}.json' for x in
        ['tmp-deployments', 'tmp-assets-collateral', 'RTKN-tmp-deployments']
    ]

    cs = []

    for blob in blobs:
        with open(blob) as f:
            d = json.load(f)
            cs.extend(walk(d))

    for c, addr in cs:
        m = metas.get('.'.join(c))
        if m:
            (abi, ast) = abi_and_ast(m)
            cli.add_command(contract_interface(c[-1], addr, abi, ast), name=c[-1])

def contract_interface(name: str, addr: str, abi, ast):
    @click.group(name=name)
    def group():
        pass
    group.name == name

    rw = {
        'pure': 'read',
        'view': 'read',
        'nonpayable': 'write',
        'payable': 'write',
    }

    def fn_interface(name, inputs, x):
        mutability = rw[x["stateMutability"]]

        @group.command(
            name=name,
            params=[click.Argument([i['name']]) for i in inputs],
            short_help=f'''{mutability}\t({
                ', '.join(f"{i['type']} {i['name']}" for i in inputs)
            })''',
            help=(ast.get(name) or {}).get('text', '').replace('\n', '\n\n'),
        )
        def f(**kwargs):
            subprocess.check_call([
                'cast',
                'call' if mutability == 'read' else 'send',
                '--mnemonic', 'mnemonic.txt',
                addr,
                f'''{name}({
                    ','.join(i['type'] for i in x['inputs'])
                })({
                    ','.join(o['type'] for o in x['outputs'])
                })''',
            ] + [
                kwargs[arg['name']] for arg in x['inputs']
            ])

        f.name == name

        return f

    for x in abi:
        if x['type'] == 'function':
            fn_interface(x['name'], x['inputs'], x)

    return group

if __name__ == '__main__':
    setup()
    cli()
