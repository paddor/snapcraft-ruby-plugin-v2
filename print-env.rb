#!/usr/bin/env ruby

puts "ENV:"
ENV.each do |k,v|
  puts "#{k} => #{v}"
end

puts "load paths:"
puts $:

puts "loaded:"
puts $"
