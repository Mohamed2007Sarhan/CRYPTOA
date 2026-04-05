"""
Backtester — Test Mode: Estimates and verifies accuracy
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from core.indicators import compute_all_indicators
from core.strategy_manager import StrategyManager


class BacktestResult:
    def __init__(self):
        self.trades:        List[dict] = []
        self.total_trades:  int = 0
        self.winning:       int = 0
        self.losing:        int = 0
        self.win_rate:      float = 0.0
        self.total_pnl:     float = 0.0
        self.max_drawdown:  float = 0.0
        self.sharpe_ratio:  float = 0.0
        self.best_trade:    float = 0.0
        self.worst_trade:   float = 0.0
        self.avg_gain:      float = 0.0
        self.avg_loss:      float = 0.0

    def to_dict(self) -> dict:
        return {
            "total_trades":  self.total_trades,
            "winning":       self.winning,
            "losing":        self.losing,
            "win_rate":      round(self.win_rate, 1),
            "total_pnl":     round(self.total_pnl, 2),
            "max_drawdown":  round(self.max_drawdown, 2),
            "sharpe_ratio":  round(self.sharpe_ratio, 2),
            "best_trade":    round(self.best_trade, 2),
            "worst_trade":   round(self.worst_trade, 2),
            "avg_gain":      round(self.avg_gain, 2),
            "avg_loss":      round(self.avg_loss, 2),
        }


class Backtester:
    def __init__(self, strategy_manager: StrategyManager):
        self.strategy_mgr = strategy_manager

    def run(self,
            df: pd.DataFrame,
            strategy_name: str,
            initial_capital: float = 1000.0,
            risk_pct: float = 1.0,
            stop_loss_pct: float = 2.0,
            take_profit_pct: float = 4.0,
            lookback: int = 50,
            ) -> BacktestResult:
        """
        Runs Backtest on historical data.
        Takes a sliding window of data and applies the strategy.
        """
        result = BacktestResult()
        capital = initial_capital
        peak_capital = initial_capital
        pnl_list = []

        if len(df) < lookback + 10:
            return result

        in_trade = False
        entry_price = 0.0
        trade_side  = ""
        trade_amount = 0.0

        for i in range(lookback, len(df) - 1):
            window = df.iloc[i - lookback: i + 1].copy()
            indicators = compute_all_indicators(window)
            current_price = float(df.iloc[i]["close"])
            next_price    = float(df.iloc[i + 1]["close"])

            if not in_trade:
                signal = self.strategy_mgr.apply_strategy(strategy_name, indicators)
                if signal in ("BUY", "SELL"):
                    trade_amount = (capital * risk_pct / 100) / current_price
                    entry_price  = current_price
                    trade_side   = signal
                    in_trade     = True
                    sl_price = (entry_price * (1 - stop_loss_pct / 100)
                                if trade_side == "BUY"
                                else entry_price * (1 + stop_loss_pct / 100))
                    tp_price = (entry_price * (1 + take_profit_pct / 100)
                                if trade_side == "BUY"
                                else entry_price * (1 - take_profit_pct / 100))
            else:
                # Check Stop Loss and Take Profit
                hit_sl = (next_price <= sl_price if trade_side == "BUY"
                          else next_price >= sl_price)
                hit_tp = (next_price >= tp_price if trade_side == "BUY"
                          else next_price <= tp_price)

                if hit_sl or hit_tp:
                    exit_price = tp_price if hit_tp else sl_price
                    pnl = ((exit_price - entry_price) * trade_amount
                           if trade_side == "BUY"
                           else (entry_price - exit_price) * trade_amount)
                    capital  += pnl
                    in_trade  = False
                    pnl_list.append(pnl)

                    trade_record = {
                        "idx":        i,
                        "side":       trade_side,
                        "entry":      round(entry_price, 4),
                        "exit":       round(exit_price, 4),
                        "pnl":        round(pnl, 4),
                        "pnl_pct":    round((pnl / (entry_price * trade_amount)) * 100, 2),
                        "outcome":    "WIN" if pnl > 0 else "LOSS",
                        "date":       str(df.index[i]),
                    }
                    result.trades.append(trade_record)

                    if capital > peak_capital:
                        peak_capital = capital
                    drawdown = (peak_capital - capital) / peak_capital * 100
                    result.max_drawdown = max(result.max_drawdown, drawdown)

        # Final Statistics
        result.total_trades = len(result.trades)
        if result.total_trades > 0:
            wins  = [t for t in result.trades if t["outcome"] == "WIN"]
            losses = [t for t in result.trades if t["outcome"] == "LOSS"]
            result.winning   = len(wins)
            result.losing    = len(losses)
            result.win_rate  = (result.winning / result.total_trades) * 100
            result.total_pnl = sum(t["pnl"] for t in result.trades)
            result.best_trade  = max((t["pnl"] for t in result.trades), default=0)
            result.worst_trade = min((t["pnl"] for t in result.trades), default=0)
            result.avg_gain = (sum(t["pnl"] for t in wins) / len(wins)) if wins else 0
            result.avg_loss = (sum(t["pnl"] for t in losses) / len(losses)) if losses else 0

            # Sharpe Ratio
            if pnl_list:
                returns = np.array(pnl_list)
                result.sharpe_ratio = (
                    (returns.mean() / (returns.std() + 1e-9)) * np.sqrt(252)
                )

        return result

    def run_all_strategies(self, df: pd.DataFrame,
                           **kwargs) -> Dict[str, BacktestResult]:
        """Tests all strategies"""
        results = {}
        for name in self.strategy_mgr.list_strategies():
            results[name] = self.run(df, name, **kwargs)
        return results

    def ai_prediction_test(self, df: pd.DataFrame,
                            ai_predictions: List[dict]) -> dict:
        """
        Verifies AI prediction accuracy on actual data.
        Every prediction: {index, decision, confidence}
        """
        correct = 0
        wrong   = 0
        total   = len(ai_predictions)

        for pred in ai_predictions:
            idx      = pred.get("index", 0)
            decision = pred.get("decision", "HOLD")
            if idx + 1 >= len(df):
                continue
            current = float(df.iloc[idx]["close"])
            next_p  = float(df.iloc[idx + 1]["close"])
            actual_move = "BUY" if next_p > current else "SELL"
            if decision == actual_move:
                correct += 1
            elif decision != "HOLD":
                wrong += 1

        accuracy = (correct / (correct + wrong) * 100) if (correct + wrong) > 0 else 0
        return {
            "total_predictions": total,
            "correct":  correct,
            "wrong":    wrong,
            "accuracy": round(accuracy, 1),
        }
