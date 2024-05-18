"""
Copyright (C) 2019 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
 and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.
"""

from ibapi.object_implem import Object
from ibapi.order import Order
from ibapi.tag_value import TagValue


class AvailableAlgoParams(Object):

    # ! [scale_params]
    @staticmethod
    def FillScaleParams(baseOrder: Order, scaleInitLevelSize: int, scaleSubsLevelSize: int, scaleRandomPercent: bool,
                        scalePriceIncrement: float, scalePriceAdjustValue: float, scalePriceAdjustInterval: int,
                        scaleProfitOffset: float, scaleAutoReset: bool, scaleInitPosition: int, scaleInitFillQty: int):
        baseOrder.scaleInitLevelSize = scaleInitLevelSize  # Initial Component Size
        baseOrder.scaleSubsLevelSize = scaleSubsLevelSize  # Subsequent Comp. Size
        baseOrder.scaleRandomPercent = scaleRandomPercent  # Randomize size by +/-55%
        baseOrder.scalePriceIncrement = scalePriceIncrement  # Price Increment

        # Auto Price adjustment
        baseOrder.scalePriceAdjustValue = scalePriceAdjustValue  # starting price by
        baseOrder.scalePriceAdjustInterval = scalePriceAdjustInterval  # in seconds

        # Profit Orders
        baseOrder.scaleProfitOffset = scaleProfitOffset  # Create profit taking order Profit Offset
        baseOrder.scaleAutoReset = scaleAutoReset  # Restore size after taking profit
        baseOrder.scaleInitPosition = scaleInitPosition  # Initial Position
        baseOrder.scaleInitFillQty = scaleInitFillQty  # Filled initial Component Size
    # ! [scale_params]

    # ! [arrivalpx_params]
    @staticmethod
    def FillArrivalPriceParams(baseOrder: Order, maxPctVol: float,
                               riskAversion: str, startTime: str, endTime: str,
                               forceCompletion: bool, allowPastTime: bool):
        baseOrder.algoStrategy = "ArrivalPx"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("maxPctVol", maxPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("riskAversion", riskAversion))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("endTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("forceCompletion",  # type: ignore
                                             int(forceCompletion)))  # type: ignore
        baseOrder.algoParams.append(TagValue("allowPastEndTime",  # type: ignore
                                             int(allowPastTime)))  # type: ignore

    # ! [arrivalpx_params]
    # ! [darkice_params]
    @staticmethod
    def FillDarkIceParams(baseOrder: Order, displaySize: int, startTime: str,
                          endTime: str, allowPastEndTime: bool):
        baseOrder.algoStrategy = "DarkIce"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("displaySize", displaySize))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("endTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("allowPastEndTime",  # type: ignore
                                             int(allowPastEndTime)))  # type: ignore

    # ! [darkice_params]

    # ! [pctvol_params]
    @staticmethod
    def FillPctVolParams(baseOrder: Order, pctVol: float, startTime: str,
                         endTime: str, noTakeLiq: bool):
        baseOrder.algoStrategy = "PctVol"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("pctVol", pctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("endTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("noTakeLiq", int(noTakeLiq)))  # type: ignore

    # ! [pctvol_params]

    # ! [twap_params]
    @staticmethod
    def FillTwapParams(baseOrder: Order, strategyType: str, startTime: str,
                       endTime: str, allowPastEndTime: bool):
        baseOrder.algoStrategy = "Twap"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("strategyType", strategyType))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("endTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("allowPastEndTime",  # type: ignore
                                             int(allowPastEndTime)))  # type: ignore

    # ! [twap_params]

    # ! [vwap_params]
    @staticmethod
    def FillVwapParams(baseOrder: Order, maxPctVol: float, startTime: str,
                       endTime: str, allowPastEndTime: bool, noTakeLiq: bool):
        baseOrder.algoStrategy = "Vwap"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("maxPctVol", maxPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("endTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("allowPastEndTime",  # type: ignore
                                             int(allowPastEndTime)))  # type: ignore
        baseOrder.algoParams.append(TagValue("noTakeLiq", int(noTakeLiq)))  # type: ignore

    # ! [vwap_params]

    # ! [ad_params]
    @staticmethod
    def FillAccumulateDistributeParams(baseOrder: Order, componentSize: int,
                                       timeBetweenOrders: int, randomizeTime20: bool, randomizeSize55: bool,
                                       giveUp: int, catchUp: bool, waitForFill: bool, startTime: str,
                                       endTime: str):
        baseOrder.algoStrategy = "AD"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("componentSize", componentSize))  # type: ignore
        baseOrder.algoParams.append(TagValue("timeBetweenOrders", timeBetweenOrders))  # type: ignore
        baseOrder.algoParams.append(TagValue("randomizeTime20",  # type: ignore
                                             int(randomizeTime20)))  # type: ignore
        baseOrder.algoParams.append(TagValue("randomizeSize55",  # type: ignore
                                             int(randomizeSize55)))  # type: ignore
        baseOrder.algoParams.append(TagValue("giveUp", giveUp))  # type: ignore
        baseOrder.algoParams.append(TagValue("catchUp", int(catchUp)))  # type: ignore
        baseOrder.algoParams.append(TagValue("waitForFill", int(waitForFill)))  # type: ignore
        baseOrder.algoParams.append(TagValue("activeTimeStart", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("activeTimeEnd", endTime))  # type: ignore

    # ! [ad_params]

    # ! [balanceimpactrisk_params]
    @staticmethod
    def FillBalanceImpactRiskParams(baseOrder: Order, maxPctVol: float,
                                    riskAversion: str, forceCompletion: bool):
        baseOrder.algoStrategy = "BalanceImpactRisk"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("maxPctVol", maxPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("riskAversion", riskAversion))  # type: ignore
        baseOrder.algoParams.append(TagValue("forceCompletion",  # type: ignore
                                             int(forceCompletion)))  # type: ignore

    # ! [balanceimpactrisk_params]

    # ! [minimpact_params]
    @staticmethod
    def FillMinImpactParams(baseOrder: Order, maxPctVol: float):
        baseOrder.algoStrategy = "MinImpact"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("maxPctVol", maxPctVol))  # type: ignore

    # ! [minimpact_params]

    # ! [adaptive_params]
    @staticmethod
    def FillAdaptiveParams(baseOrder: Order, priority: str):
        baseOrder.algoStrategy = "Adaptive"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("adaptivePriority", priority))  # type: ignore

    # ! [adaptive_params]

    # ! [closepx_params]
    @staticmethod
    def FillClosePriceParams(baseOrder: Order, maxPctVol: float, riskAversion: str,
                             startTime: str, forceCompletion: bool):
        baseOrder.algoStrategy = "ClosePx"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("maxPctVol", maxPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("riskAversion", riskAversion))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("forceCompletion", int(forceCompletion)))  # type: ignore

    # ! [closepx_params]

    # ! [pctvolpx_params]
    @staticmethod
    def FillPriceVariantPctVolParams(baseOrder: Order, pctVol: float,
                                     deltaPctVol: float, minPctVol4Px: float,
                                     maxPctVol4Px: float, startTime: str,
                                     endTime: str, noTakeLiq: bool):
        baseOrder.algoStrategy = "PctVolPx"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("pctVol", pctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("deltaPctVol", deltaPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("minPctVol4Px", minPctVol4Px))  # type: ignore
        baseOrder.algoParams.append(TagValue("maxPctVol4Px", maxPctVol4Px))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("endTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("noTakeLiq", int(noTakeLiq)))  # type: ignore

    # ! [pctvolpx_params]

    # ! [pctvolsz_params]
    @staticmethod
    def FillSizeVariantPctVolParams(baseOrder: Order, startPctVol: float,
                                    endPctVol: float, startTime: str,
                                    endTime: str, noTakeLiq: bool):
        baseOrder.algoStrategy = "PctVolSz"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("startPctVol", startPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("endPctVol", endPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("endTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("noTakeLiq", int(noTakeLiq)))  # type: ignore

    # ! [pctvolsz_params]

    # ! [pctvoltm_params]
    @staticmethod
    def FillTimeVariantPctVolParams(baseOrder: Order, startPctVol: float,
                                    endPctVol: float, startTime: str,
                                    endTime: str, noTakeLiq: bool):
        baseOrder.algoStrategy = "PctVolTm"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("startPctVol", startPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("endPctVol", endPctVol))  # type: ignore
        baseOrder.algoParams.append(TagValue("startTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("endTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("noTakeLiq", int(noTakeLiq)))  # type: ignore

    # ! [pctvoltm_params]

    # ! [jefferies_vwap_params]
    @staticmethod
    def FillJefferiesVWAPParams(baseOrder: Order, startTime: str,
                                endTime: str, relativeLimit: float,
                                maxVolumeRate: float, excludeAuctions: str,
                                triggerPrice: float, wowPrice: float,
                                minFillSize: int, wowOrderPct: float,
                                wowMode: str, isBuyBack: bool, wowReference: str):
        # must be direct-routed to "JEFFALGO"
        baseOrder.algoStrategy = "VWAP"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("StartTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("EndTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("RelativeLimit", relativeLimit))  # type: ignore
        baseOrder.algoParams.append(TagValue("MaxVolumeRate", maxVolumeRate))  # type: ignore
        baseOrder.algoParams.append(TagValue("ExcludeAuctions", excludeAuctions))  # type: ignore
        baseOrder.algoParams.append(TagValue("TriggerPrice", triggerPrice))  # type: ignore
        baseOrder.algoParams.append(TagValue("WowPrice", wowPrice))  # type: ignore
        baseOrder.algoParams.append(TagValue("MinFillSize", minFillSize))  # type: ignore
        baseOrder.algoParams.append(TagValue("WowOrderPct", wowOrderPct))  # type: ignore
        baseOrder.algoParams.append(TagValue("WowMode", wowMode))  # type: ignore
        baseOrder.algoParams.append(TagValue("IsBuyBack", int(isBuyBack)))  # type: ignore
        baseOrder.algoParams.append(TagValue("WowReference", wowReference))  # type: ignore
    # ! [jefferies_vwap_params]

    # ! [csfb_inline_params]
    @staticmethod
    def FillCSFBInlineParams(baseOrder: Order, startTime: str,
                             endTime: str, execStyle: str,
                             minPercent: int, maxPercent: int,
                             displaySize: int, auction: str,
                             blockFinder: bool, blockPrice: float,
                             minBlockSize: int, maxBlockSize: int, iWouldPrice: float):
        # must be direct-routed to "CSFBALGO"
        baseOrder.algoStrategy = "INLINE"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("StartTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("EndTime", endTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("ExecStyle", execStyle))  # type: ignore
        baseOrder.algoParams.append(TagValue("MinPercent", minPercent))  # type: ignore
        baseOrder.algoParams.append(TagValue("MaxPercent", maxPercent))  # type: ignore
        baseOrder.algoParams.append(TagValue("DisplaySize", displaySize))  # type: ignore
        baseOrder.algoParams.append(TagValue("Auction", auction))  # type: ignore
        baseOrder.algoParams.append(TagValue("BlockFinder", int(blockFinder)))  # type: ignore
        baseOrder.algoParams.append(TagValue("BlockPrice", blockPrice))  # type: ignore
        baseOrder.algoParams.append(TagValue("MinBlockSize", minBlockSize))  # type: ignore
        baseOrder.algoParams.append(TagValue("MaxBlockSize", maxBlockSize))  # type: ignore
        baseOrder.algoParams.append(TagValue("IWouldPrice", iWouldPrice))  # type: ignore
    # ! [csfb_inline_params]

    # ! [qbalgo_strobe_params]
    @staticmethod
    def FillQBAlgoInLineParams(baseOrder: Order, startTime: str,
                               endTime: str, duration: float,
                               benchmark: str, percentVolume: float,
                               noCleanUp: bool):
        # must be direct-routed to "QBALGO"
        baseOrder.algoStrategy = "STROBE"
        baseOrder.algoParams = []  # type: ignore
        baseOrder.algoParams.append(TagValue("StartTime", startTime))  # type: ignore
        baseOrder.algoParams.append(TagValue("EndTime", endTime))  # type: ignore
        # This example uses endTime instead of duration
        # baseOrder.algoParams.append(TagValue("Duration", str(duration)))
        baseOrder.algoParams.append(TagValue("Benchmark", benchmark))   # type: ignore
        baseOrder.algoParams.append(TagValue("PercentVolume", str(percentVolume)))  # type: ignore
        baseOrder.algoParams.append(TagValue("NoCleanUp", int(noCleanUp)))  # type: ignore
    # ! [qbalgo_strobe_params]


def Test():
    av = AvailableAlgoParams()  # @UnusedVariable
    print(f"AV: {av}")


if "__main__" == __name__:
    Test()
