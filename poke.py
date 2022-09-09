import json
import os
import pathlib
import subprocess

import click

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

@click.group()
def cli():
    pass

def setup():
    rsr_dir = pathlib.Path.home() / 'src' / 'github.com' / 'reserve-protocol' / 'protocol'

    os.chdir(rsr_dir)

    chainid = 31337

    blobs = [
        f'{chainid}-{x}.json' for x in
        ['RTKN-tmp-deployments', 'tmp-assets-collateral', 'tmp-deployments']
    ]

    artifacts = subprocess.check_output([
        'fd', '-e', 'json', '-E', '*.dbg.json', '.', 'artifacts/contracts',
    ]).decode().split()

    def walk(d, prefix=[]):
        res = []
        for k, v in d.items():
            if type(v) is str:
                res.append((prefix + [k], v))
            else:
                res.extend(walk(v, prefix + [k]))
        return res

    cs = []

    def lookup_artifact(name: str):
        name = name[0].capitalize() + name[1:]
        for a in artifacts:
            if a.endswith(f'{name}.json'):
                return a
            if a.endswith(f'{name}P1.json'):
                return a
        return None

    for blob in blobs:
        with open(blob) as f:
            d = json.load(f)
            cs.extend(walk(d))

    yes = 0
    no = 0

    for c, addr in cs:
        a = lookup_artifact(c[-1])
        if a:
            yes += 1
            with open(a) as f:
                abi = json.load(f)['abi']
            with open(a.replace('.json', '.dbg.json')) as f:
                buildInfo = json.load(f)['buildInfo']
            # with open(buildInfo) as f:
                # json.load(f)['output']['sources']['contracts'][
            cli.add_command(contract_interface(c[-1], addr, abi), name=c[-1])
        else:
            no += 1

def contract_interface(name: str, addr: str, abi):
    @click.group(name=name)
    def group():
        pass
    group.name == name

    def fn_interface(name, inputs):
        @group.command(
            name=name,
            params=[click.Argument([i['name']]) for i in inputs],
            short_help=f'''({
                ', '.join(f"{i['type']} {i['name']}" for i in inputs)
            })''',
        )
        def f():
            print(f.name)
        f.name == name

        return f

    for x in abi:
        if x['type'] == 'function':
            fn_interface(x['name'], x['inputs'])

    return group

if __name__ == '__main__':
    setup()
    cli()
