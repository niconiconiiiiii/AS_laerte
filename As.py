import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime

# ------------ api -------------- #
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUyNjA3NDA1LCJpYXQiOjE3NTAwMTU0MDUsImp0aSI6ImQ5NTQzMGU3YjQxMTQyNGY5ZjhkNGRkMWZlMDcyZTdlIiwidXNlcl9pZCI6NjV9.TLjoZ9Zp1oGWm-WA_0M9YQLKDA1nBXqzWymB82msQdA"
headers = {'Authorization': 'JWT {}'.format(token)}

# ---------- request preco corrigido em determinado range ----------- # 
def fetch_preco_corrigido(ticker, data_ini, data_fim):
    
    print(f"Buscando dados de {ticker} de {data_ini} ate {data_fim}...") # debug
    
    # parametros
    params = {
        'ticker': ticker,
        'data_ini': data_ini,
        'data_fim': data_fim
    }
    
    try:
        r = requests.get('https://laboratoriodefinancas.com/api/v1/preco-corrigido', params=params, headers=headers) # request
        r.raise_for_status() # debug
        
        resp = r.json() # resposta
        


        dados = resp['dados'] #lista


        df = pd.DataFrame(dados)


        df['data'] = pd.to_datetime(df['data'])
        df = df.set_index('data').sort_index()

        
        return df

    except requests.exceptions.RequestException as e:
        print(f"Deu erro processando a resposta {ticker}: {e}")
        if r.content:
            print(f"Resposta da api {ticker}: {r.content.decode('utf-8')}")
        return pd.DataFrame()

# ---------- top 10 magic formula ----------- # 

params_planilhao = {'data_base': '2024-01-02'}


r_planilhao = requests.get('https://laboratoriodefinancas.com/api/v1/planilhao', params=params_planilhao, headers=headers) # request
r_planilhao.raise_for_status() # debug

dados_planilhao = r_planilhao.json()['dados'] # resposta
    


df_planilhao = pd.DataFrame(dados_planilhao)

# filtro
df_filtered = df_planilhao.dropna(subset=['earning_yield', 'roic', 'ticker'])
df_filtered = df_filtered[(df_filtered['earning_yield'].notna()) & (df_filtered['roic'].notna())] 
df_filtered = df_filtered[(df_filtered['earning_yield'] > -10) & (df_filtered['roic'] > -10)] 

# ranqueia baseado em earning_yield e roic
df_filtered['rank_earnings_yield'] = df_filtered['earning_yield'].rank(ascending=False)
df_filtered['rank_roic'] = df_filtered['roic'].rank(ascending=False)

# soma os rankings para fazer o ranking final
df_filtered['magic_formula_rank'] = df_filtered['rank_earnings_yield'] + df_filtered['rank_roic']

# Seleciona os 10 melhores
top_10_stocks = df_filtered.sort_values(by='magic_formula_rank').head(10)
tickers_selecionados = top_10_stocks['ticker'].tolist()

print("\nTop 10 Ações pela Magic Formula (02/Jan/2024):")
print(top_10_stocks[['ticker', 'magic_formula_rank', 'earning_yield', 'roic']])

print(f"\nTickers selecionados para análise de desempenho: {tickers_selecionados}") # debug


# ---------- avaliacao de performance para grafico ----------- # 

start_date_performance = '2024-01-02'
end_date_performance = '2024-12-30' 

cumulative_returns_df = pd.DataFrame()
individual_total_returns = {}

for ticker in tickers_selecionados:
    df_prices = fetch_preco_corrigido(ticker, start_date_performance, end_date_performance)

    
    daily_returns = df_prices['fechamento'].pct_change()
    cumulative_return = (1 + daily_returns.fillna(0)).cumprod()
    
    # ratio de preco ini / preco final
    cumulative_return = cumulative_return / cumulative_return.iloc[0]
    
    cumulative_returns_df[ticker] = cumulative_return
    
    initial_price = df_prices['fechamento'].iloc[0]
    final_price = df_prices['fechamento'].iloc[-1]
    total_return_percentage = ((final_price - initial_price) / initial_price) * 100
    individual_total_returns[ticker] = total_return_percentage


print("\n--- Total Returns (02/Jan/2024 - 30/Dec/2024) ---") # retorno %

for ticker, ret in individual_total_returns.items():
    print(f"{ticker}: {ret:.2f}%")



# grafico
if not cumulative_returns_df.empty: # debug

    plt.figure(figsize=(16, 9)) 
    
    for column in cumulative_returns_df.columns:
        plt.plot(cumulative_returns_df.index, cumulative_returns_df[column], label=column, linewidth=1.5)

    plt.title('Performance usando Magic Formula ações (Jan 2, 2024 - Dec 30, 2024)', fontsize=16)
    plt.xlabel('Data', fontsize=12)
    plt.ylabel('Retorno acumulado (pr inicio / pr final)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.axhline(y=1, color='gray', linestyle='-', linewidth=1.0, label='Inicio (1.0)') # Solid line for starting point
    
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Tickers")
    
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    plt.show()
else:
    print("Dados insuficientres para grafico erro")