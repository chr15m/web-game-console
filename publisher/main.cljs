(ns main
  {:clj-kondo/config '{:lint-as {promesa.core/let clojure.core/let}}}
  (:require
    [reagent.core :as r]
    [reagent.dom :as rdom]
    [promesa.core :as p]))

(def emojis ["🌟" "🍄" "🔥" "💧" "💎" "🍌" "🍎" "🍀" "👻" "💀" "👽" "🤖" "💣" "🔔" "💙" "🌙"])
(def max-size-bytes (* 128 1024))
(def relays ["wss://relay.mccormick.cx"])

(defonce state (r/atom {:sk nil
                        :pk nil
                        :npub nil
                        :files []
                        :game-name nil
                        :zip-base64 nil
                        :stats nil
                        :game-code nil
                        :publishing? false
                        :error nil
                        :history {}
                        :show-modal? false}))

(defn load-history []
  (when-let [stored (js/localStorage.getItem "wgc-publisher-history")]
    (try
      (let [parsed (js->clj (js/JSON.parse stored) :keywordize-keys true)]
        (js/console.log "DEBUG: Loaded history from localStorage:" (clj->js parsed))
        (swap! state assoc :history parsed))
      (catch js/Error e
        (js/console.error "DEBUG: Error loading history:" e)))))

(defn save-history [history]
  (js/localStorage.setItem "wgc-publisher-history" (js/JSON.stringify (clj->js history))))

(defn hex->bytes [hex]
  (let [bytes (js/Uint8Array. (/ (.-length hex) 2))]
    (dotimes [i (.-length bytes)]
      (aset bytes i (js/parseInt (.substr hex (* i 2) 2) 16)))
    bytes))

(defn bytes->hex [bytes]
  (.join (.map (js/Array.from bytes)
               #(-> % (.toString 16) (.padStart 2 "0")))
         ""))

(defn generate-or-load-keys []
  (let [stored (js/localStorage.getItem "wgc-publisher-sk")]
    (if stored
      (let [sk (hex->bytes stored)
            pk (js/NostrTools.getPublicKey sk)
            npub (js/NostrTools.nip19.npubEncode pk)]
        (swap! state assoc :sk sk :pk pk :npub npub))
      (let [sk (js/NostrTools.generateSecretKey)
            pk (js/NostrTools.getPublicKey sk)
            npub (js/NostrTools.nip19.npubEncode pk)]
        (js/localStorage.setItem "wgc-publisher-sk" (bytes->hex sk))
        (swap! state assoc :sk sk :pk pk :npub npub)))))

(defn handle-file-select [e]
  (let [files (array-seq (.. e -target -files))]
    (swap! state assoc :files files :zip-base64 nil :stats nil :error nil :game-code nil)
    (when (seq files)
      (let [zip (js/JSZip.)
            first-path (.-webkitRelativePath (first files))
            game-name (if (seq first-path) (first (.split first-path "/")) "unknown")]
        (js/console.log "DEBUG: Selected game-name:" game-name)
        (swap! state assoc :game-name game-name)
        (doseq [file files]
          (let [path (.-webkitRelativePath file)
                clean-path (if (seq path)
                             (let [parts (.split path "/")]
                               (.join (.slice parts 1) "/"))
                             (.-name file))]
            (.file zip clean-path file)))
        (p/let [base64 (.generateAsync zip #js {:type "base64"
                                                :compression "DEFLATE"
                                                :compressionOptions #js {:level 9}})]
          (let [size-bytes (js/Math.floor (* (/ (.-length base64) 4) 3))]
            (if (> size-bytes max-size-bytes)
              (swap! state assoc :error (str "Bundle too large: " size-bytes " bytes (max " max-size-bytes ")"))
              (swap! state assoc
                     :zip-base64 base64
                     :stats {:count (count files)
                             :size size-bytes}))))))))

(defn generate-game-code [pk-hex salt-num]
  (let [pk-bytes (hex->bytes pk-hex)
        salt-bytes (js/Uint8Array. 4)
        view (js/DataView. (.-buffer salt-bytes))]
    (.setUint32 view 0 salt-num true)
    (let [concat-bytes (js/Uint8Array. (+ (.-length pk-bytes) 4))]
      (.set concat-bytes pk-bytes 0)
      (.set concat-bytes salt-bytes (.-length pk-bytes))
      (p/let [hash-buffer (js/crypto.subtle.digest "SHA-256" concat-bytes)
              hash-array (js/Uint8Array. hash-buffer)
              code-bytes (.slice hash-array 0 8)
              code-emojis (mapcat (fn [b]
                                    [(nth emojis (bit-shift-right b 4))
                                     (nth emojis (bit-and b 0x0F))])
                                  (array-seq code-bytes))]
        (apply str code-emojis)))))

(defn slice-emojis [code n]
  (.join (.slice (js/Array.from code) 0 n) ""))

(defn publish! []
  (swap! state assoc :publishing? true :error nil)
  (let [{:keys [sk pk zip-base64 game-name history]} @state
        game-key (keyword game-name)
        existing (get history game-key)
        salt (if existing (:salt existing) (js/Math.floor (* (js/Math.random) 0xFFFFFFFF)))]
    (js/console.log "DEBUG: publish! called")
    (js/console.log "DEBUG: game-name (string):" game-name)
    (js/console.log "DEBUG: game-key (keyword):" (str game-key))
    (js/console.log "DEBUG: current history keys:" (clj->js (keys history)))
    (js/console.log "DEBUG: existing entry found?:" (some? existing))
    (js/console.log "DEBUG: existing data:" (clj->js existing))
    (js/console.log "DEBUG: using salt:" salt)
    (p/let [code (generate-game-code pk salt)
            event-template #js {:kind 30078
                                :created_at (js/Math.floor (/ (js/Date.now) 1000))
                                :tags #js [#js ["d" code]
                                           #js ["t" (str "wgc5-" (slice-emojis code 5))]
                                           #js ["t" (str "wgc7-" (slice-emojis code 7))]
                                           #js ["t" (str "wgc9-" (slice-emojis code 9))]
                                           #js ["wgc_m" (str salt)]]
                                :content zip-base64}
            event (js/NostrTools.finalizeEvent event-template sk)
            pool (js/NostrTools.SimplePool.)]
      (-> (js/Promise.any (.publish pool (clj->js relays) event))
          (.then (fn [_]
                   (let [new-history (assoc history game-key
                                            {:salt salt
                                             :code code
                                             :event-id (.-id event)
                                             :updated-at (.toISOString (js/Date.))})]
                     (save-history new-history)
                     (swap! state assoc :publishing? false :game-code code :history new-history)
                     (.close pool (clj->js relays)))))
          (.catch (fn [e]
                    (swap! state assoc :publishing? false :error (str "Publish failed: " e))
                    (.close pool (clj->js relays))))))))

(defn copy-to-clipboard [e text]
  (let [el (.-currentTarget e)]
    (-> (js/navigator.clipboard.writeText text)
        (.then (fn []
                 (.add (.-classList el) "notify")
                 (js/setTimeout #(.remove (.-classList el) "notify") 2000))))))

(defn upload-modal []
  (let [{:keys [stats error game-code publishing?]} @state]
    [:dialog {:open true}
     [:div
      [:h3 (if game-code "Success!" "Upload Game")]
      
      (if game-code
        [:div
         [:p "Your game has been published. Here is your Game Code:"]
         [:div.game-code-display.copyable 
          {:data-notification-text "Copied!"
           :on-click #(copy-to-clipboard % game-code)}
          game-code]
         [:div.dialog-actions
          [:button {:on-click #(swap! state assoc :show-modal? false :game-code nil :stats nil)} "Close"]]]
        
        [:div
         (when-not stats
           [:div
            [:label "Select Game Folder"]
            [:input {:type "file"
                     :webkitdirectory "true"
                     :directory "true"
                     :on-change handle-file-select}]])
         
         (when error
           [:p.error error])
         
         (when stats
           [:div
            [:p "Files: " (:count stats)]
            [:p "Compressed Size: " (:size stats) " bytes"]
            [:div.dialog-actions
             [:button {:on-click publish!
                       :disabled publishing?}
              (if publishing? "Publishing..." "Publish to Nostr")]
             [:button {:type "reset" :on-click #(swap! state assoc :show-modal? false :stats nil :error nil)} "Cancel"]]])
         
         (when (and (not stats) (not publishing?))
           [:div.dialog-actions
            [:button {:type "reset" :on-click #(swap! state assoc :show-modal? false :error nil)} "Cancel"]])])]]))

(defn app []
  (let [{:keys [npub history show-modal?]} @state]
    [:div#app
     [:header.spread
      [:div.clickable
       [:svg.logo-icon [:use {:href "#icon-sun"}]]
       [:strong " web game console"]]
      [:nav
       [:action-buttons
        [:span {:style {:font-size "0.8em" :color "var(--shade)"}} 
         (when npub (str (subs npub 0 12) "..." (subs npub (- (count npub) 4))))]
        [:svg [:use {:href "#icon-user"}]]]]]

     [:main
      [:section
       [:h2 "Published Games"]
       (if (seq history)
         [:table.history-table
          [:thead
           [:tr
            [:th "Folder"]
            [:th "Game Code"]
            [:th "Actions"]]]
          [:tbody
           (for [[gkey data] history]
             ^{:key gkey}
             [:tr
              [:td (name gkey)]
              [:td.copyable {:data-notification-text "Copied!"
                             :on-click #(copy-to-clipboard % (:code data))}
               [:code {:style {:letter-spacing "2px"}} (:code data)]]
              [:td
               [:button {:on-click #(swap! state assoc :show-modal? true :game-name (name gkey))}
                [:svg.icon-sm [:use {:href "#icon-upload"}]]]]])]]
         [:p "No games published yet."])
       
       [:div.plus-btn-container
        [:button.plus-btn {:on-click #(swap! state assoc :show-modal? true :game-name nil)} "+"]]]]

     (when show-modal?
       [upload-modal])

     [:footer]]))

(defn ^:export init []
  (generate-or-load-keys)
  (load-history)
  (rdom/render [app] (.getElementById js/document "app")))

(init)
