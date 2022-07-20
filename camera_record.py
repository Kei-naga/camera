import cv2
import time
import datetime
import numpy as np
import psutil
import os

##############################################################
#####################  調整  ##################################
# 動画格納場所のパス
videopath = '/Volumes/USB_memo/camera/'
# 対応コーデックを指定
codec = 'mp4v'
# 保存動画の拡張子指定
ext = '.mp4'
# 動画の変化率
d = 0.0008
# 加重平均の重み
weight = 0.6
# 中央値フィルタのカーネル
size_kernel = 11
##############################################################
##############################################################

class Camera():
    def __init__(self):
        pass

    # 動体検知
    def moving(self, frame, acc):
        # グレースケールに変換
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # cv2.imshow("test",gray)
        # 比較用frame取得
        if acc is None:
            acc = gray.copy().astype("float")
        # 加重平均を累積して計算(重みは０.5)
        cv2.accumulateWeighted(gray, acc, weight)
        # 画像配列の差を計算
        frame_d = cv2.absdiff(gray, cv2.convertScaleAbs(acc))
        # 変化量が3以上で閾値処理
        thresh = cv2.threshold(frame_d, 3, 255, cv2.THRESH_BINARY)[1]
        # 中央値フィルタによるノイズ除去
        thresh = cv2.medianBlur(thresh, size_kernel)
        cv2.imshow("test", thresh)
        # どれだけ変化したか
        delta = np.sum(thresh) / 255 / thresh.size
        # print(delta)
        # 変化量と累積器を返す
        return delta, acc

    # 容量測定＋削除
    def delete(self):
        # ディスク使用率を取得
        dsk = psutil.disk_usage(videopath)
        # ディスク使用率95%以上の場合
        while dsk.percent > 95.0 == True:
            filelists = []
            # ファイルを取得
            for file in os.listdir():
                base, f_ext = os.path.splitext(file)
                # 動画ファイルだけリストで保存
                if f_ext == ext:
                    # [ファイル名]
                    filelists.append(os.path.basename(base))
            # ファイルを並び替え
            filelists.sort()
            # 一番古いファイルを指定
            remove_file = os.remove(videopath+filelists[0]+ext)

    def frames(self):
        # 動画取得
        cap = cv2.VideoCapture(0)
        # 解像度の設定
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # 時間を取得
        date = datetime.datetime.now().strftime("%Y%m%d%H")
        # 記録ファイルを開く(OSXでのコーデック)
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(str(videopath) + date +
                              ext, fourcc, 20, (width, height))
        # 累積器を用意
        accumulator = None
        # 待機時間
        time.sleep(2)

        # frameごとに繰り返す
        while True:
            # 空き容量をチェック
            self.delete()
            # frameを取得(retは読み込めたかを判定)
            ret, frame = cap.read()
            if not ret:
                break
            # 左右反転
            frame = cv2.flip(frame, 1)
            # 動体検知
            delta, accumulator = self.moving(frame, accumulator)
            # 一定変化量(0.1%)を超えたら記録
            if delta > d: #調整
                # 現在日付を取得
                nowdate = datetime.datetime.now().strftime("%Y%m%d%H")
                # 時間ごとにファイル切替
                if date != nowdate:
                    date = nowdate
                    out.release()
                    # 新たなファイル作成
                    out = cv2.VideoWriter(
                        str(videopath) + date + ext, fourcc, 20, (width, height))
                # frameをファイルに書き込む
                out.write(frame)
                # 結果のframeを表示
                cv2.imshow(str(date), frame)

            # qで終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # 表示ウィンドウを閉じる
        cap.release()
        out.release()
        cv2.destroyAllWindows()

# 実行
camera = Camera()
camera.frames()
