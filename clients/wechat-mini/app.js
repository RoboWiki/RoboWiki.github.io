App({
  globalData: { dataVersion: '' },
  onLaunch() {
    wx.showShareMenu({
      menus: ['shareAppMessage', 'shareTimeline'],
    })
  },
})
