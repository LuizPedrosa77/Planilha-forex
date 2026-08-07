//+------------------------------------------------------------------+
//|                                                      GPFX_Sync.mq5 |
//| Robo de sincronizacao: envia o historico de operacoes fechadas    |
//| do MT5 para o Supabase (via Edge Function ingest-trades).         |
//|                                                                  |
//| Como usar:                                                       |
//|  1. Gere sua chave de API na planilha (Configuracoes > Robo MT5)  |
//|  2. Cole a chave no input "InpApiKey" abaixo                      |
//|  3. Libere a URL em: Ferramentas > Opcoes > Expert Advisors >     |
//|     "Permitir WebRequest para as URLs listadas" > adicione a URL  |
//|     da sua funcao (InpApiUrl)                                     |
//|  4. Anexe este EA a qualquer grafico e deixe "AutoTrading" ligado |
//+------------------------------------------------------------------+
#property copyright "Gustavo Pedrosa FX"
#property version   "1.00"
#property strict

input string InpApiUrl           = "https://qvenzhntgaogbbvxwgjd.supabase.co/functions/v1/ingest-trades";
input string InpApiKey           = "COLE_AQUI_SUA_CHAVE_GERADA_NA_PLANILHA";
input string InpAccountLabel     = "";      // opcional: rotulo da conta (default = numero da conta)
input int    InpSyncIntervalSecs = 300;     // sincroniza a cada 5 minutos
input bool   InpSendFullHistoryOnInit = true;

datetime g_lastSyncTime = 0;
string   g_gvName;

//+------------------------------------------------------------------+
int OnInit()
{
   g_gvName = "GPFX_LastSync_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));

   if(GlobalVariableCheck(g_gvName))
      g_lastSyncTime = (datetime)GlobalVariableGet(g_gvName);

   EventSetTimer(InpSyncIntervalSecs);

   if(InpSendFullHistoryOnInit)
      SyncHistory(0); // 0 = desde o inicio (todo o historico)
   else
      SyncHistory(g_lastSyncTime);

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
}

//+------------------------------------------------------------------+
void OnTimer()
{
   // Sempre revisita um pouco antes do ultimo sync, para pegar
   // operacoes que podem ter fechado "atrasadas" (garante margem
   // de seguranca contra falhas de rede pontuais).
   datetime from = g_lastSyncTime - 604800; // 7 dias de margem (captura fechamentos parciais de posições longas)
   if(from < 0) from = 0;
   SyncHistory(from);
}

//+------------------------------------------------------------------+
//| Escaneia o historico de deals, agrupa por posicao (position id)   |
//| e envia as posicoes ja fechadas para a API.                       |
//+------------------------------------------------------------------+
void SyncHistory(datetime fromTime)
{
   if(!HistorySelect(fromTime, TimeCurrent()))
   {
      Print("GPFX_Sync: falha ao selecionar historico");
      return;
   }

   int total = HistoryDealsTotal();
   if(total <= 0) return;

   // Arrays paralelos para agregar por position_id
   long   posIds[];
   string posSymbol[];
   int    posType[];      // 0 = compra, 1 = venda (direcao da entrada)
   double posVolume[];
   double posOpenPrice[];
   double posClosePrice[];
   datetime posOpenTime[];
   datetime posCloseTime[];
   double posProfit[];
   double posSwap[];
   double posCommission[];
   bool   posClosed[];
   string posComment[];

   int count = 0;

   for(int i = 0; i < total; i++)
   {
      ulong dealTicket = HistoryDealGetTicket(i);
      if(dealTicket == 0) continue;

      long posId = HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID);
      long entry = HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
      long dtype = HistoryDealGetInteger(dealTicket, DEAL_TYPE);

      // Ignora deals que nao sao de compra/venda (balanco, credito, etc.)
      if(dtype != DEAL_TYPE_BUY && dtype != DEAL_TYPE_SELL) continue;

      // Procura se ja temos essa posicao nos arrays
      int idx = -1;
      for(int j = 0; j < count; j++)
      {
         if(posIds[j] == posId) { idx = j; break; }
      }

      if(idx == -1)
      {
         idx = count;
         count++;
         ArrayResize(posIds, count);
         ArrayResize(posSymbol, count);
         ArrayResize(posType, count);
         ArrayResize(posVolume, count);
         ArrayResize(posOpenPrice, count);
         ArrayResize(posClosePrice, count);
         ArrayResize(posOpenTime, count);
         ArrayResize(posCloseTime, count);
         ArrayResize(posProfit, count);
         ArrayResize(posSwap, count);
         ArrayResize(posCommission, count);
         ArrayResize(posClosed, count);
         ArrayResize(posComment, count);

         posIds[idx] = posId;
         posType[idx] = 0; 
         posSymbol[idx] = HistoryDealGetString(dealTicket, DEAL_SYMBOL);
         posVolume[idx] = 0;
         posOpenPrice[idx] = 0;
         posClosePrice[idx] = 0;
         posOpenTime[idx] = 0;
         posCloseTime[idx] = 0;
         posProfit[idx] = 0;
         posSwap[idx] = 0;
         posCommission[idx] = 0;
         posClosed[idx] = false;
         posComment[idx] = HistoryDealGetString(dealTicket, DEAL_COMMENT);
      }

      double dealProfit  = HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
      double dealSwap     = HistoryDealGetDouble(dealTicket, DEAL_SWAP);
      double dealComm     = HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
      double dealPrice    = HistoryDealGetDouble(dealTicket, DEAL_PRICE);
      double dealVolume   = HistoryDealGetDouble(dealTicket, DEAL_VOLUME);
      datetime dealTime   = (datetime)HistoryDealGetInteger(dealTicket, DEAL_TIME);

      posProfit[idx]     += dealProfit;
      posSwap[idx]        += dealSwap;
      posCommission[idx] += dealComm;

      if(entry == DEAL_ENTRY_IN)
      {
         posOpenPrice[idx] = dealPrice;
         posOpenTime[idx]  = dealTime;
         posVolume[idx]    = dealVolume;
         posType[idx]      = (int)dtype; // direcao da entrada
      }
      else if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY)
      {
         posClosePrice[idx] = dealPrice;
         posCloseTime[idx]  = dealTime;
         posClosed[idx]     = true;
      }
   }

   // Monta o JSON só com as posições fechadas
   string json = "{\"account_id\":\"" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "\",";
   json += "\"trades\":[";

   int sent = 0;
   for(int k = 0; k < count; k++)
   {
      if(!posClosed[k]) continue; // ainda aberta, nao envia

      if(sent > 0) json += ",";
      json += "{";
      json += "\"ticket\":\"" + IntegerToString(posIds[k]) + "\",";
      json += "\"symbol\":\"" + JsonEscape(posSymbol[k]) + "\",";
      json += "\"action\":\"" + (string)(posType[k] == DEAL_TYPE_BUY ? "Buy" : "Sell") + "\",";
      json += "\"volume\":" + DoubleToString(posVolume[k], 2) + ",";
      json += "\"open_time\":" + (posOpenTime[k] == 0 ? "null" : "\"" + TimeToIso(posOpenTime[k]) + "\"") + ",";
      json += "\"close_time\":" + (posCloseTime[k] == 0 ? "null" : "\"" + TimeToIso(posCloseTime[k]) + "\"") + ",";
      json += "\"open_price\":" + DoubleToString(posOpenPrice[k], 5) + ",";
      json += "\"close_price\":" + DoubleToString(posClosePrice[k], 5) + ",";
      json += "\"profit\":" + DoubleToString(posProfit[k], 2) + ",";
      json += "\"swap\":" + DoubleToString(posSwap[k], 2) + ",";
      json += "\"commission\":" + DoubleToString(posCommission[k], 2) + ",";
      json += "\"comment\":\"" + JsonEscape(posComment[k]) + "\"";
      json += "}";
      sent++;
   }
   json += "]}";

   if(sent == 0)
   {
      Print("GPFX_Sync: nenhuma posicao fechada nova para enviar.");
      return;
   }

   if(SendToApi(json))
   {
      g_lastSyncTime = TimeCurrent();
      GlobalVariableSet(g_gvName, (double)g_lastSyncTime);
      Print("GPFX_Sync: ", sent, " operacoes enviadas com sucesso.");
   }
}

//+------------------------------------------------------------------+
bool SendToApi(string jsonBody)
{
   string headers = "Content-Type: application/json\r\nx-api-key: " + InpApiKey + "\r\n";
   uchar data[];
   uchar result[];
   string resultHeaders;

   int len = StringToCharArray(jsonBody, data, 0, WHOLE_ARRAY, CP_UTF8) - 1;
   ArrayResize(data, len);

   ResetLastError();
   int status = WebRequest("POST", InpApiUrl, headers, 5000, data, result, resultHeaders);

   if(status == -1)
   {
      int err = GetLastError();
      Print("GPFX_Sync: erro no WebRequest (", err, "). Verifique se a URL esta liberada em ",
            "Ferramentas > Opcoes > Expert Advisors > Permitir WebRequest.");
      return false;
   }

   string response = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);

   if(status != 200)
   {
      Print("GPFX_Sync: resposta inesperada (HTTP ", status, "): ", response);
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
string TimeToIso(datetime t)
{
   if(t == 0) return "";
   string d = TimeToString(t, TIME_DATE);   // formato: yyyy.mm.dd
   StringReplace(d, ".", "-");
   string tm = TimeToString(t, TIME_SECONDS); // formato: hh:mm:ss
   return d + "T" + tm + "Z";
}

//+------------------------------------------------------------------+
string JsonEscape(string s)
{
   string out = s;
   StringReplace(out, "\\", "\\\\");
   StringReplace(out, "\"", "\\\"");
   StringReplace(out, "\n", " ");
   StringReplace(out, "\r", " ");
   StringReplace(out, "\t", " ");
   return out;
}
//+------------------------------------------------------------------+